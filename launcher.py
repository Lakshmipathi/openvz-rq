from rq import Connection, Queue, Worker
from redis import Redis
from tasks import create_container
import time

# Tell RQ what Redis connection to use
with Connection(Redis()):
    q = Queue('creatq')  # no args implies the default queue



d_os={}
###EDIT ME
d_os['cid']="200" #cid=uid
#d_os['ostemplate']="altlinux-3.0"
d_os['ostemplate']="custom"
#d_os['ostemplate']="ubuntu-13.04-x86"
d_os['proceed_nextq']=True
d_os['move_to_stopq']=False
d_os['num_instance']=1
d_os['ipadd']="10.2.0.131"
d_os['hname']="test44"
d_os['nserver']="10.121.12.31"
d_os['usr']="root"
d_os['pwd']="a"
d_os['container_uptime']=20
###EDIT ME

for i in range(1,2):
	d_os['cid']=str(600+i)
	d_os['ipadd']="10.2.0."+str(i)
	d_os['hname']="test"+str(i)

	job = q.enqueue_call(func=create_container,args=(d_os,),result_ttl=-1)

	print job.result   # => 89
