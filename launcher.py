from rq import Connection, Queue, Worker
from redis import Redis
from tasks import create_container
import time

# Tell RQ what Redis connection to use
with Connection(Redis()):
    q = Queue('creatq')  # no args implies the default queue



d_os={}
###EDIT ME
d_os['ct_type']="aws_vm"

if d_os['ct_type'] is "openvz":
    d_os['cid']="200" #cid=uid
    #d_os['ostemplate']="altlinux-20060914-x86_64"
    d_os['ostemplate']="centos-6-x86_64"
    d_os['ipadd']="10.2.0.1"
    d_os['hname']="test44"
    d_os['nserver']="172.31.0.2"
    d_os['usr']="root"
    d_os['pwd']="a"
else: #docker
    d_os['repo']=" laks/3.4"
    d_os['port']=" -p 3000:3000"
    d_os['ct_cmd']=" /bin/bash"
    d_os['docker_cmd']=" run"
    d_os['options'] = " -i -t -d"
    d_os['imgid'] = ""

#common keys
d_os['container_uptime']=300
d_os['proceed_nextq']=True
d_os['move_to_stopq']=True
d_os['num_instance']=1
d_os['username']="kamalg"
###EDIT ME


if d_os['ct_type'] == "openvz":
    for i in range(1,5):
	d_os['cid']=str(500+i)
	d_os['ipadd']="10.2.0."+str(i)
	d_os['hname']="webminal"+str(i)

	job = q.enqueue_call(func=create_container,args=(d_os,),result_ttl=600,timeout=600)
	print job.result   
else:
	job = q.enqueue_call(func=create_container,args=(d_os,),result_ttl=600,timeout=600)
	print job.result  
