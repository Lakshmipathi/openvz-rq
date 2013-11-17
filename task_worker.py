from rq import Connection, Queue, Worker
from redis import Redis
import time,os,multiprocessing

def q_err_handler(job, exc_type, exc_value, traceback):
   with open("/tmp/q.fail","a") as fd:
       fd.write("\n**********FAIL******")
       fd.write("\ntype:"+str(exc_type))
       fd.write("\nvalue:"+str(exc_value))
       fd.write("\ntraceback:"+str(traceback))
       fd.write("\n*********FAIL******")
   return False


def q_worker(qname):
	with Connection(Redis()):
	    q = Queue(qname)
	    w = Worker([q],exc_handler=q_err_handler)
	    w.work()


##EDIT ME
no_of_worker_threads = 8

if __name__ == '__main__':
    qnames_list=['creatq','setupq','startq','stopq','destroyq']

    for qname in qnames_list * no_of_worker_threads:
         multiprocessing.Process(target=q_worker,args=(qname,)).start()
