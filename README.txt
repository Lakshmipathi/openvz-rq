openvz-rq - Python-rq based framework for OpenVZ:
------------------------------------------------

Step 1)launcher.py -> Which will be invoked from website code when user places a request.
With user input as dictionary (d_os -> property of os)
launcher places a request into 'creatq' when user places this request.

[ tasks.py -> has individual basic task methods like creat_container,setup_container,start_container,
stop_container,destroy_container. ]

#################################################################
### Task Flow  : creatq=>setupq=>startq=>stop=>destroyq
################################################################

Step 2)creat_container : once processed the 'vnctl create' command, will place request into 
'setupq' to setup ipaddress,hostname,nameserver etc.

Step 3)setup_container : will set request configs and moves it to 'startq'

Step 4) Start_container : which listens to 'startq' and picks up any arriving item and starts the container
Here as of now, It waits for 20 seconds then moves the container to 'stopq'

Step 5) Stop_container : Will stop the container id picked up from 'stopq' . Places it to 'destroyq'

Step 6) destroy_container  : does destroy the container. 

[ task_worker.py -> this file has the actual worker which will invoke above functions when something
arrives at the 'queue'. And does error handling as described below]

Error handling :
----------------
In case of any failure with their Queue operation , logs will be placed under appropriate file 
like /tmp/creatq.fail,/tmp/setupq.fail etc  We can easily add these error to 'errorq' and use 
mail_function to notify us these errors.



Installation:
=============
yum install redis-server 
yum install python-setuptools

easy_install python-rq
easy_install requests

How to use these programs:
--------------------------
First edit 'launcher.py with your openvz template,id,ipaddress etc details.

Now, run 
redis-server #start the redis-server 
python launcher.py #places request to creatq

#to process the request. Run
python task_worker.py 

--
make sure you run 'vzlist -a' on another terminal to view the progress. 
If you don't want the container to be terminated after 20 seconds,increase 
the time by editing 'time.sleep(20)' in tasks.py file.


Write to <lakshmipathi.g@giis.co.in> for any questions/suggestions/feedback.

