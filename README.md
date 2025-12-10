1. Project.mn and project_delay.mn are the two technologies
2. File name with B500M is for throughput = 500Mbps, file name with B10M is for throughput = 10Mbps
3. Project_topo_exp1 is for the task 4 in the proposal
4. Project_topo_exp2 is for the task 5 in the proposal
5. Project_topo_exp3 is for the task 6 in the proposal
6. Analyze_logs is for task 7

To run, put all files into mininet->examples, then run "sudo mn -c",
then if you want to run throughput = 10M, run "sudo python3 project_topo_exp1_B10M",
then "sudo python3 project_topo_exp2_B10M", 
then "sudo python3 project_topo_exp3_B10M", 
then "python3 analyze_logs", it will print everything on the cmd and output log files, and it will also create 4 plots for each statistics collection.
