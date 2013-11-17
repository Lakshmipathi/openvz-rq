import requests,os,time,subprocess,shlex
from rq import Connection, Queue, Worker
from redis import Redis

def display_date():
        cmd = " date +%m_%d_%y_%M_%s "
        out = subprocess.check_output(shlex.split(cmd))
        return out


#################################################################
### Task Flow  : creatq=>setupq=>startq=>stop=>destroyq
################################################################

#stage-1 Create container
#cid == uid of the user , num == no.of instances to create
def create_container(d_os):
    num = d_os['num_instance']
    while num > 0:
	    cmd="vzctl create "+d_os['cid']+" --ostemplate "+ d_os['ostemplate'] 
	    print cmd 
	    out = subprocess.check_output(shlex.split(cmd))
	    num -= 1

    if d_os['proceed_nextq'] :
	    with Connection(Redis()):
		q=Queue('setupq')
  	        job = q.enqueue_call(func=setup_container,args=(d_os,),result_ttl=-1)

#stage-2 Setup configuration
def setup_container(d_os):
	cmd="vzctl set "+d_os['cid']+" --ipadd "+d_os['ipadd']+" --hostname "+d_os['hname']+" --nameserver "+d_os['nserver']+" --userpasswd "+d_os['usr']+":"+d_os['pwd']+" --save"
	print cmd
	out = subprocess.check_output(shlex.split(cmd))

        #next queue
        if d_os['proceed_nextq'] :
    	     with Connection(Redis()):
		q=Queue('startq')
  		job = q.enqueue_call(func=start_container,args=(d_os,),result_ttl=-1)


#stage-3 start cid
def start_container(d_os):
	cmd="vzctl start "+d_os['cid']
	print cmd
	out = subprocess.check_output(shlex.split(cmd))

	time.sleep(d_os['container_uptime'])
        #next queue
        if d_os['proceed_nextq'] and d_os['move_to_stopq']:
    	   with Connection(Redis()):
		q=Queue('stopq')
		job = q.enqueue_call(func=stop_container,args=(d_os,),result_ttl=-1)
	else:
	   print "Keep the containers running."


#stage-4 stop cid
def stop_container(d_os):
	cmd="vzctl stop "+d_os['cid']
	print cmd
	out = subprocess.check_output(shlex.split(cmd))

        #next queue
        if d_os['proceed_nextq'] :
    	   with Connection(Redis()):
		q=Queue('destroyq')
		job = q.enqueue_call(func=destroy_container,args=(d_os,),result_ttl=-1)


#stage-5 destroy cid
def destroy_container(d_os):
	cmd="vzctl destroy "+d_os['cid']
	print cmd
	out = subprocess.check_output(shlex.split(cmd))
