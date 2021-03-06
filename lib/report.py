import os
import bleach
from bleach.sanitizer import Cleaner
import lib.db
import urllib
import time

def paths_report(host):
    all_paths = lib.db.get_all_paths_for_host(host)
    html_code = ""
    for row in all_paths:
        ip,port,path,url_screenshot_filename,workspace = row
        try:
            os.stat(url_screenshot_filename)
            url_screenshot_filename = urllib.quote(url_screenshot_filename)
            url_screenshot_filename_relative = os.path.join("screens/",url_screenshot_filename.split("/screens/")[1])
            html_code = html_code + """\n<div id="linkwrap">\n"""
            html_code = html_code + """<a class="link" href="#">[Screenshot]<span><img src="{1}" alt="image"/></span></a>  <a href="{0}">{0}</a><br>\n""".format(path,url_screenshot_filename_relative)
            html_code = html_code + "\n</div>\n"
        except:
            #print("Could not find screenshot for " + path)
            html_code = html_code + """\n<div id="linkwrap">\n"""
            html_code = html_code + "[Screenshot]  " + """<a href="{0}">{0}</a><br>\n""".format(path)
            html_code = html_code + "\n</div>\n"
    return html_code


def report(workspace,target_list=None):

    cleaner = Cleaner()
    report_count = 0

    host_report_file_names = []
    if target_list:
        #TODO for loop around targets in scope or somethign...
        a=""
    else:
        #unique_hosts = lib.db.get_unique_hosts_in_workspace(workspace)
        unique_ips = lib.db.get_unique_hosts(workspace)
        unique_vhosts = lib.db.get_unique_inscope_vhosts(workspace)
        if len(unique_ips) == 0:
            print("[!] - There are no hosts in the [{0}] workspace. Try another?\n".format(workspace))
            exit()

    print("\n[+] Generating a report for the [" + workspace + "] workspace (" + str(len(unique_ips)) +") unique IP(s) and (" + str(len(unique_vhosts)) + ") unique vhosts(s)\n")

    # HTML Report
    output_dir = lib.db.get_output_dir_for_workspace(workspace)[0][0]
    workspace_report_directory = os.path.join(output_dir, "celerystalkReports")
    try:
        os.stat(workspace_report_directory)
    except:
        os.mkdir(workspace_report_directory)

    combined_report_file_name = os.path.join(workspace_report_directory,'Celerystalk-Workspace-Report[' + workspace + '].html')
    combined_report_file = open(combined_report_file_name, 'w')
    combined_report_file.write(populate_report_head())


    for ip in unique_ips:
        ip = ip[0]
        unique_vhosts_for_ip = lib.db.get_unique_inscope_vhosts_for_ip(ip, workspace)

        #unique_vhosts_for_ip.append(ip) # This line makes sure the report includes the tools run against the IP itself.
        for vhost in unique_vhosts_for_ip:
            vhost = vhost[0]

            host_report_file_name = os.path.join(workspace_report_directory,vhost + '_hostReport.txt')
            host_report_file_names.append([vhost,host_report_file_name])
            host_report_file = open(host_report_file_name, 'w')
            populate_report_data(host_report_file,vhost,workspace)
            host_report_file.close()
            print("[+] Report file (single host): {0}".format(host_report_file_name))



    # Create sidebar navigation
    for vhost,report in sorted(host_report_file_names):
        #TODO: This is static and will be buggy. I think i need to use a regex here to get the hostname which is in between /hostname/celerystalkoutput
        #host=report.split("/celerystalkOutput")[0].split("/")[2]
        combined_report_file.write("""  <a href="#{0}">{0}</a>\n""".format(vhost))



    #HTML Report header
    combined_report_file.write("""</div>
<div class="main">

<h1 id="top">celerystalk Report</h1>
\n""")


    #Text Report
    combined_report_file_name_txt = os.path.join(workspace_report_directory,'Celerystalk-Workspace-Report[' + workspace + '].txt')
    combined_report_file_txt = open(combined_report_file_name_txt, 'w')
    unique_command_names = lib.db.get_unique_command_names(workspace)
    filter_html_body = '''<div id="myBtnContainer">\n'''
    filter_html_body = filter_html_body + '''<button class="btn active" onclick="filterSelection('all')"> Show all</button>\n'''
    filter_html_body = filter_html_body + '''<button class="btn" onclick="filterSelection('services')"> Services</button>\n'''
    filter_html_body = filter_html_body + '''<button class="btn" onclick="filterSelection('paths')"> Paths</button>\n'''

    for command_name in unique_command_names:
        command_name = command_name[0]
        filter_html_body = filter_html_body + "<button class=\"btn\" onclick=\"filterSelection(\'{0}\')\"> {0}</button>\n".format(command_name)
    filter_html_body = filter_html_body + "\n</div>"

    combined_report_file.write(filter_html_body)
    # Create the rest of the report
    for vhost,report in sorted(host_report_file_names):
        report_string = ""
        ip = lib.db.get_vhost_ip(vhost,workspace)
        ip = ip[0][0]
        services = lib.db.get_all_services_for_ip(ip,workspace)

        #Text report
        #These lines write to the parent report file (1 report for however many hosts)
        combined_report_file_txt.write('*' * 80 + '\n\n')
        combined_report_file_txt.write('  ' + "Host Report:" + report + '\n')
        combined_report_file_txt.write('\n' + '*' * 80 + '\n\n')

        #These lines write to the parent report file (1 report for however many hosts)
        combined_report_file.write("""<a name="{0}"></a><br>\n""".format(vhost))
        combined_report_file.write("""<h2>Host Report: {0}</h2>\n""".format(vhost))
        #TODO: print services for each host - but onlyh for hte ip??
        services_table_html = "<table><tr><th>Port</th><th>Protocol</th><th>Service</th></tr>"
        for id,ip,port,proto,service,workspace in services:
            services_table_html = services_table_html + "<tr>\n<td>{0}</td>\n<td>{1}</td>\n<td>{2}</td>\n</tr>\n".format(port,proto,service)
        services_table_html = services_table_html + "</table>\n<br>\n"

        combined_report_file.write('''\n<div class="filterDiv services">\n''')
        combined_report_file.write(services_table_html)
        combined_report_file.write("\n</div>")


        screenshot_html = paths_report(vhost)

        combined_report_file.write('''\n\n<div class="filterDiv paths">\n''')
        combined_report_file.write(screenshot_html + "\n<br>")
        combined_report_file.write("\n</div>\n")

        #Generate the html code for all of that command output and headers
        report_host_string = populate_report_data_html(vhost, workspace)
        report_string = report_string + report_host_string
        #combined_report_file.write('</pre>\n')
        combined_report_file.write(report_string)


    combined_report_file.write("\n\n")
    combined_report_file_txt.write("\n\n")



        # with open(report, 'r') as host_report_file:
        #     #Generate html that has each path with a screenshot per line
        #     screenshot_html = paths_report(host)
        #     combined_report_file.write(screenshot_html)
        #
        #     combined_report_file.write('<pre>\n')
        #
        #
        #     for line in host_report_file:
        #         #HTML report
        #         line = unicode(line, errors='ignore')
        #         try:
        #             sanitized = bleach.clean(line)
        #         except:
        #             print("[!] Could not output santize the following line (Not including it in report to be safe):")
        #             print("     " + line)
        #             sanitized = ""
        #
        #         combined_report_file.write(sanitized)
        #         #txt Report
        #         combined_report_file_txt.write(line)
        #     combined_report_file.write('</pre>\n')

    # for ip in unique_ips:
    #     ip = ip[0]
    #     services = lib.db.get_all_services_for_ip(ip, workspace)
    #
    #     unique_vhosts_for_ip = lib.db.get_unique_inscope_vhosts_for_ip(ip, workspace)
    #
    #     # unique_vhosts_for_ip.append(ip) # This line makes sure the report includes the tools run against the IP itself.
    #
    #     for vhost in unique_vhosts_for_ip:
    #         vhost = vhost[0]
    #
    #         #Generate html that has each path with a screenshot per line
    #         screenshot_html = paths_report(vhost)
    #         combined_report_file.write(screenshot_html)
    #
    #         #Generate the html code for all of that command output and headers
    #         report_host_string = populate_report_data_html(vhost, workspace)
    #         report_string = report_string + report_host_string
    #     combined_report_file.write('</pre>\n')
    #     combined_report_file.write(report_string)
    #
    #
    #     combined_report_file.write("\n\n")
    #     combined_report_file_txt.write("\n\n")


    report_footer = """
<script>
var coll = document.getElementsByClassName("collapsible");
var i;

for (i = 0; i < coll.length; i++) {
  coll[i].addEventListener("click", function() {
    this.classList.toggle("active");
    var content = this.nextElementSibling;
    if (content.style.display === "block") {
      content.style.display = "none";
    } else {
      content.style.display = "block";
    }
  });
}
</script>

<script>
filterSelection("all")
function filterSelection(c) {
  var x, i;
  x = document.getElementsByClassName("filterDiv");
  if (c == "all") c = "";
  for (i = 0; i < x.length; i++) {
    w3RemoveClass(x[i], "show");
    if (x[i].className.indexOf(c) > -1) w3AddClass(x[i], "show");
  }
}

function w3AddClass(element, name) {
  var i, arr1, arr2;
  arr1 = element.className.split(" ");
  arr2 = name.split(" ");
  for (i = 0; i < arr2.length; i++) {
    if (arr1.indexOf(arr2[i]) == -1) {element.className += " " + arr2[i];}
  }
}

function w3RemoveClass(element, name) {
  var i, arr1, arr2;
  arr1 = element.className.split(" ");
  arr2 = name.split(" ");
  for (i = 0; i < arr2.length; i++) {
    while (arr1.indexOf(arr2[i]) > -1) {
      arr1.splice(arr1.indexOf(arr2[i]), 1);     
    }
  }
  element.className = arr1.join(" ");
}

// Add active class to the current button (highlight it)
var btnContainer = document.getElementById("myBtnContainer");
var btns = btnContainer.getElementsByClassName("btn");
for (var i = 0; i < btns.length; i++) {
  btns[i].addEventListener("click", function(){
    var current = document.getElementsByClassName("active");
    current[0].className = current[0].className.replace(" active", "");
    this.className += " active";
  });
}
</script>



"""

    combined_report_file.write(report_footer)
    combined_report_file.close()
    combined_report_file_txt.close()


    print("\n[+] Report file (All workspace hosts): {0} (has screenshots!!!)".format(combined_report_file_name))
    print("[+] Report file (All workspace hosts): {0}\n".format(combined_report_file_name_txt))
    print("\n[+] For quick access, open with local firefox (works over ssh with x forwarding):\n")
    print("firefox " + combined_report_file_name + " &\n")
    print("[+] Or you can copy the celerystalkReports folder, which contains everything you need to view the report\n")


def populate_report_head():
    #https: // www.w3schools.com / howto / howto_css_fixed_sidebar.asp
    web_head =  ("""<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body {
    font-family: "Lato", sans-serif;
    font-size: 16px;
}

table {
}

th, td {
    text-align: left;
    padding: 8px;
    border-radius: 5px;
    -moz-border-radius: 5px;
    padding: 5px;
}

tr:nth-child(even){background-color: #f2f2f2}

th {
    background-color: #777;
    color: white;
    padding: 4px;

}

.sidenav {
    width: 160px;
    position: fixed;
    z-index: 1;
    top: 0;
    left: 0;
    bottom: 0;
    background: #eee;
    overflow-x: auto;
    overflow-y: auto
    padding: 8px 0;
    display: block;
}

.sidenav a {
    padding: 6px 8px 6px 16px;
    text-decoration: none;
    font-size: 12px;
    color: #2196F3;
    display: block;
}

.sidenav a:hover {
    color: #064579;
}

.main {
    margin-left: 170px; /* Same width as the sidebar + left position in px */
    font-size: 14px; /* Increased text to enable scrolling */
    padding: 0px 10px;
}

@media screen and (max-height: 450px) {
    .sidenav {padding-top: 15px;}
    .sidenav a {font-size: 18px;}
}

#linkwrap {
    position:relative;

}
.link img { 
    border:5px solid gray;
    margin:3px;
    float:left;
    width:100%;
    border-style: outset;
    border-radius: 25px;
    display:block;
    position:relative;    
}
.link span { 
    position:absolute;
    visibility:hidden;
    font-size: 16px;
}
.link:hover, .link:hover span { 
    visibility:visible;
    top:0; left:280px; 
    z-index:1;
}
.collapsible {
    background-color: #777;
    color: white;
    cursor: pointer;
    padding: 4px;
    width: 90%;
    border: none;
    border-radius: 12px;
    text-align: left;
    text-indent: 5px;    
    outline: none;
    font-size: 12px;
}

.active, .collapsible:hover {
    background-color: #555;
}

.content {
    padding: 0 18px;
    display: none;
    overflow: hidden;
    background-color: #f1f1f1;    
}


.filterDiv {
  margin: 2px;
  display: none;
}

.show {
  display: block;
}

.container {
  margin-top: 10px;
  
}

/* Style the buttons */
.btn {
  border: none;
  outline: none;
  background-color: #f1f1f1;
  border-radius: 12px;
  padding: 8px;
  font-size: 14px;

}

.btn:hover {
  background-color: #ddd;
}

.btn.active {
  background-color: #666;
  color: white;
}

</style>
</head>
<body>


<div class="sidenav">
<a href="#top">Top</a>\n""")
    return web_head


def populate_report_data(report_file,vhost,workspace):
    """

    :param report_file:
    :param vhost:
    :param workspace:
    :return:
    """

    reportable_output_files_for_vhost = lib.db.get_reportable_output_files_for_vhost(workspace,vhost)
    for vhost_output_file in reportable_output_files_for_vhost:
        vhost_output_file = vhost_output_file[0]
        normalized_output_file = os.path.normpath(vhost_output_file)
        tasks_for_output_file = lib.db.get_tasks_for_output_file(workspace,vhost,vhost_output_file)
        for command_name,command,status,start_time,run_time in tasks_for_output_file:
            #Don't print header info for simulation jobs
            if not command.startswith('#'):
                try:
                    if os.stat(normalized_output_file).st_size == 0:
                        report_file.write('\n')
                        report_file.write('-' * 50 + '\n')
                        report_file.write("Command Name:\t" + command_name + " (No data produced)\n")

                        # report_file.write("{0} did not produce any data\n".format(command_name))
                        report_file.write('-' * 50)
                    else:
                        report_file.write('\n\n')
                        report_file.write('-' * 50 + '\n')
                        report_file.write("Command Name:\t" + command_name + '\n')
                        report_file.write("Start Time:\t" + start_time + '\n')
                        if status == "COMPLETED":
                            report_file.write("Run Time:\t" + run_time + '\n')
                        report_file.write("Command:\t" + command + '\n')
                        report_file.write("Output File:\t" + normalized_output_file + '\n')
                        report_file.write("Status:\t\t" + status + '\n')
                        report_file.write('-' * 50 + '\n\n')
                except OSError, e:
                    report_file.write('\n')
                    report_file.write('-' * 50 + '\n')
                    report_file.write("Command Name:\t" + command_name+ '\n')
                    report_file.write("Command:\t" + command + '\n')
                    report_file.write("\nNo such file or directory: " + normalized_output_file + "\n")
                    # report_file.write("{0} did not produce any data\n".format(command_name))
                    report_file.write('-' * 50)



        linecount = 0
        try:
            with open(normalized_output_file, "r") as scan_file:
                for line in scan_file:
                    if linecount < 300:
                        report_file.write(line)
                    linecount = linecount + 1
                if linecount > 300:
                    report_file.write("\nSnip... Only displaying first 300 of the total " + str(
                        linecount) + " lines...\n")
        except IOError, e:
            #dont tell the user at the concole that file didnt exist.
            pass


def populate_report_data_html(vhost,workspace):
    """

    :param report_file:
    :param vhost:
    :param workspace:
    :return:
    """
    report_host_html_string = ""
    reportable_output_files_for_vhost = lib.db.get_reportable_output_files_for_vhost(workspace,vhost)
    for vhost_output_file in reportable_output_files_for_vhost:
        vhost_output_file = vhost_output_file[0]
        normalized_output_file = os.path.normpath(vhost_output_file)
        tasks_for_output_file = lib.db.get_tasks_for_output_file(workspace,vhost,vhost_output_file)
        for command_name,command,status,start_time,run_time in tasks_for_output_file:
            #print(run_time)
            #print(type(start_time))
            start_time = time.strftime("%m/%d/%Y %H:%M:%S",time.localtime(float(start_time)))
            if run_time:
                run_time = time.strftime('%H:%M:%S', time.gmtime(float(run_time)))

            #Don't print header info for simulation jobs
            if not command.startswith('#'):
                #report_host_html_string = report_host_html_string + "</pre>\n"
                report_host_html_string = report_host_html_string + '''<div class="filterDiv ''' + command_name + '''">\n'''

                report_host_html_string = report_host_html_string + '''<button class="collapsible">''' + command_name + '''</button>\n'''
                report_host_html_string = report_host_html_string + '''<div class="content">'''
                report_host_html_string = report_host_html_string + '''<table>'''
                try:
                    report_host_html_string = report_host_html_string +  "<tr><td>Start Time:</td><td>" + start_time + '</td></tr>\n'
                    if status == "COMPLETED":
                        report_host_html_string = report_host_html_string +  "<tr><td>Run Time:</td><td>" + run_time + '</td></tr>\n'
                    report_host_html_string = report_host_html_string +  "<tr><td>Command:</td><td>" + command + '</td></tr>\n'
                    report_host_html_string = report_host_html_string +  "<tr><td>Output File:</td><td>" + normalized_output_file + '</td></tr>\n'
                    if os.stat(normalized_output_file).st_size == 0:
                        report_host_html_string = report_host_html_string +  "<tr><td>Status:</td><td>" + status + ' [No Output Data]</td></tr>\n'
                    else:
                        report_host_html_string = report_host_html_string + "<tr><td>Status:</td><td>" + status + '</td></tr>\n'
                except OSError, e:
                    report_host_html_string = report_host_html_string +  "<tr><td>Command:</td><td>" + command + '</td></tr>\n'
                    report_host_html_string = report_host_html_string +  "\nError!: No such file or directory: " + normalized_output_file + "</td></tr>\n"
                    # report_host_html_string = report_host_html_string +  "{0} did not produce any data\n".format(command_name))
                report_host_html_string = report_host_html_string +  "</table>\n</div>\n"


        #This is the part that reads the contents of each output file
        linecount = 0
        report_host_html_string = report_host_html_string + "        <pre>"
        try:
            with open(normalized_output_file, "r") as scan_file:
                for line in scan_file:
                    line = unicode(line, errors='ignore')
                    try:
                        sanitized = bleach.clean(line)
                    except:
                        print(
                            "[!] Could not output santize the following line (Not including it in report to be safe):")
                        print("     " + line)
                        sanitized = ""
                    if linecount < 300:
                        report_host_html_string = report_host_html_string + sanitized
                    linecount = linecount + 1
                if linecount > 300:
                    report_host_html_string = report_host_html_string +  "\nSnip... Only displaying first 300 of the total " + str(
                        linecount) + " lines...\n"
        except IOError, e:
            #dont tell the user at the concole that file didnt exist.
            pass

        report_host_html_string = report_host_html_string + "        </pre>\n</div>\n"
    return report_host_html_string


