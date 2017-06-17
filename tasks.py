import requests,os,time,subprocess,shlex,re
from rq import Connection, Queue, Worker, get_current_job
from redis import Redis
import spoty
import programmingsite

def check_output(*popenargs, **kwargs):
    r"""Run command with arguments and return its output as a byte string.
 
    Backported from Python 2.7 as it's implemented as pure python on stdlib.
 
    >>> check_output(['/usr/bin/python', '--version'])
    Python 2.6.2
    """
    process = subprocess.Popen(stdout=subprocess.PIPE, *popenargs, **kwargs)
    output, unused_err = process.communicate()
    retcode = process.poll()
    if retcode:
        cmd = kwargs.get("args")
        if cmd is None:
            cmd = popenargs[0]
        error = subprocess.CalledProcessError(retcode, cmd)
        error.output = output
        raise error
    return output


def display_date():
        cmd = " date +%m_%d_%y_%M_%s "
        out = check_output(shlex.split(cmd))
        return out

def already_running(username,code):

     if code == 0: ##do the check only for 'code' page not for distro
        return False
        # perform below for programming/code page 
        filePath = "/etc/nginx/conf.d/" 

        "replaces all string by a regex substitution"
        tempName = filePath+username+str(code)+str(".conf")
        if os.path.isfile(tempName):
              print "ct already running..we have nginx config file"
              return True
        else:
              print "no nginx conf found..proceed"
              return False

def creat_nginx_tmpl(findreplace,d_os):
        filePath = "/etc/nginx/conf.d/" 

        "replaces all string by a regex substitution"
        tempName = filePath+d_os['username']+str(".conf")
        if d_os['ct_type'] == "docker" and d_os['code'] == 1:
              tempName = filePath+d_os['username']+str(d_os['code'])+str(".conf")
        

        inputFile = open(filePath+str("vhost.template"))
        outputFile = open(tempName,'w')
        fContent = unicode(inputFile.read(), "utf-8")

        for aPair in findreplace:
            outputText = fContent.replace(aPair[0], aPair[1].rstrip())
            fContent = outputText
        outputFile.write((outputText.encode("utf-8")))

        outputFile.close()
        inputFile.close()

def reload_nginx():
        # reload apache
        cmd = "service nginx reload"
        out = check_output(shlex.split(cmd))

def setup_docker_ct_helper(d_os):
        #setup mongod files now. TODO erro checks

        #create file under /home/laks/tmp/tutorials with imgid.
        fpathname = "/home/laks/tmp/tutorials/" + str(d_os['imgid']) + ".json"
        fd = open(fpathname,"w")
        fd.write(d_os['tutorial'])
        fd.close()
        cmd = "/usr/local/bin/docker-enter " +str(d_os['imgid']) + " sh -c 'cat > /tmp/db.json' <  " + fpathname
        os.system(cmd)
        
        cmd = "/usr/local/bin/docker-enter " +str(d_os['imgid']) + " mongoimport -d test -c tutorials /tmp/db.json"
        os.system(cmd)
         
        cmd = "/usr/local/bin/docker-enter " +str(d_os['imgid']) + " rm -f /tmp/db.json"
        os.system(cmd)

        cmd = "/usr/local/bin/docker-enter " +str(d_os['imgid']) + " rm -f /.ttyjs2/app.js"
        os.system(cmd)



#################################################################
### Task Flow  : creatq=>setupq=>startq=>stop=>destroyq
################################################################

#stage-1 Create container
#cid == uid of the user , num == no.of instances to create
def create_container(d_os):
    num = d_os['num_instance']
    if d_os['ct_type'] == "docker" and already_running(d_os['username'],d_os['code']):
          print "Ignore  ct_create request"
          return

    print " -->>Running for user " + str(d_os['username']) + "with ct_type" + str(d_os['ct_type']) + "uptime is:" + str(d_os['container_uptime'])
    cur_job = get_current_job()
    cur_job.meta['ownername'] = str(d_os['username'])
    cur_job.save()
    cur_job.refresh()

    while num > 0:
            if d_os['ct_type'] == "openvz": 
          	 cmd="vzctl create "+d_os['cid']+" --ostemplate "+ d_os['ostemplate']
            elif d_os['ct_type'] == "aws_vm":
                 ec2_conn=spoty.ec2_connect()
		 config_entry =  spoty.read_conf_file(d_os['repo'])   #Read distro specific config file.
    		 cur_job.meta['request_status'] = "Reading config files"
		 cur_job.save()
		 cur_job.refresh()
                 spot,bdm = spoty.req_instance_and_tag(ec2_conn,config_entry)
    		 cur_job.meta['request_status'] = "Creating VM"
		 cur_job.save()
		 cur_job.refresh()
                 instance=spoty.set_bdm(spot,bdm,ec2_conn,config_entry)
    		 cur_job.meta['request_status'] = "Booting VM"
		 cur_job.save()
		 cur_job.refresh()
                 #push it into d_os
                 d_os['instance'] = instance
                 d_os['ec2_conn'] = ec2_conn
                 cmd = "uname -a"
            else:
		 d_os['repo_vers']='2'
		 if d_os['code'] == 1:
                      d_os['repo_vers']='3'
		      d_os['container_uptime'] = 3600
                 cmd="docker run --user wmuser --name "+ d_os['username']+str(d_os['code']) + ' ' + d_os['options']+d_os['port'] + d_os['repo'] + d_os['repo_vers'] + d_os['ct_cmd']
	    print "Starting.."
	    print cmd 
	    out = check_output(shlex.split(cmd))
	    print "Output is:"
	    print out
            d_os['imgid'] = out.rstrip()
	    num -= 1
            if d_os['code'] == 1 and  d_os['username'] == "kamalg" or  d_os['username'] == "selvaanand":
	        programmingsite.movedata_host2ct(d_os)

    if d_os['proceed_nextq'] :
	    with Connection(Redis()):
		q=Queue('setupq', default_timeout=15000)
  	        job = q.enqueue_call(func=setup_container,args=(d_os,),result_ttl=600)
    		cur_job.meta['request_status'] = "Install Software"
		cur_job.meta['setupq_jobid'] = job.id
		cur_job.save()
		cur_job.refresh()
		print cur_job.meta

#stage-2 Setup configuration
def setup_container(d_os):
     cur_job = get_current_job()
     cur_job.meta['ownername'] = str(d_os['username'])
     cur_job.meta['request_status'] = "Performing status check"
     cur_job.save()
     cur_job.refresh()
     if d_os['ct_type'] == "openvz":
	cmd="vzctl set "+d_os['cid']+" --ipadd "+d_os['ipadd']+" --hostname "+d_os['hname']+" --nameserver "+d_os['nserver']+" --userpasswd "+d_os['usr']+":"+d_os['pwd']+" --save"
	print cmd
	out = check_output(shlex.split(cmd))
     elif d_os['ct_type'] == "aws_vm":
        #create file under /home/laks/tmp/tutorials with ipaddr.
        fpathname = "/home/laks/tmp/tutorials/" + str(d_os['instance'].ip_address) + ".json"
        fd = open(fpathname,"w")
        fd.write(d_os['tutorial'])
        fd.close()

        spoty.install_sw(d_os['instance'],d_os['repo'])
        findreplace = [
        ("SUBDOMAIN",d_os['username']),
        ("IPADDRESS",d_os['instance'].ip_address)
        ]
        creat_nginx_tmpl(findreplace,d_os)
        reload_nginx()

     else:
        print "setting up subdomain for user" + str(d_os['username'])
        cmd = "docker inspect --format '{{ .NetworkSettings.IPAddress }}' " +str(d_os['imgid'])
        proc = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        ipaddr, err = proc.communicate()
        print ipaddr
        if d_os['code'] == 1:
		findreplace = [
		("SUBDOMAIN",d_os['username']+str(d_os['code'])),
		("IPADDRESS",ipaddr)
		]
        else:
		findreplace = [
		("SUBDOMAIN",d_os['username']),
		("IPADDRESS",ipaddr)
		]
        creat_nginx_tmpl(findreplace,d_os)
        reload_nginx()
        time.sleep(2)
        setup_docker_ct_helper(d_os)

     cur_job = get_current_job()
     cur_job.meta['ownername'] = str(d_os['username'])
     cur_job.meta['request_status'] = "Running, please login"
     cur_job.save()
     cur_job.refresh()
     #next queue
     if d_os['proceed_nextq'] :
           with Connection(Redis()):
         	q=Queue('startq', default_timeout=15000)
  		job = q.enqueue_call(func=start_container,args=(d_os,),result_ttl=600)

#stage-3 start cid
def start_container(d_os):
     if d_os['ct_type'] == "openvz":
	cmd="vzctl start "+d_os['cid']
	print cmd
	out = check_output(shlex.split(cmd))

     time.sleep(d_os['container_uptime'])
     #next queue
     if d_os['proceed_nextq'] and d_os['move_to_stopq']:
    	   with Connection(Redis()):
		q=Queue('stopq', default_timeout=15000)
		job = q.enqueue_call(func=stop_container,args=(d_os,),result_ttl=600)
     else:
	   print "Keep the containers running."


#stage-4 stop cid
def stop_container(d_os):
     if d_os['ct_type'] == "openvz":
	cmd="vzctl stop "+d_os['cid']
	print cmd
     elif d_os['ct_type'] == 'aws_vm':
        spoty.del_sys(d_os['instance'],d_os['ec2_conn'])
        cmd = "uptime"
     else:
	cmd="docker stop "+d_os['imgid']
	print cmd
        if d_os['code'] == 1:
	   programmingsite.movedata_ct2host(d_os)

     out = check_output(shlex.split(cmd))

     #next queue
     if d_os['proceed_nextq'] :
    	   with Connection(Redis()):
		q=Queue('destroyq', default_timeout=15000)
		job = q.enqueue_call(func=destroy_container,args=(d_os,),result_ttl=600)


#stage-5 destroy cid
def destroy_container(d_os):
     if d_os['ct_type'] == "openvz":
	cmd="vzctl destroy "+d_os['cid']
	print cmd
     elif d_os['ct_type'] == "aws_vm":
        cmd = "uptime"
     else:
	cmd="docker rm "+d_os['imgid']
	print cmd

     out = check_output(shlex.split(cmd))

     # Clean up conf file too
     filePath = "/etc/nginx/conf.d/" 
     tempName = filePath+d_os['username']+str(".conf")
     if d_os['code'] == 1:
         tempName = filePath+d_os['username']+str(d_os['code'])+str(".conf")
     cmd = "mv " +str(tempName) +" /etc/done/"
     out = check_output(shlex.split(cmd))

     # reload apache
     cmd = "service nginx reload"
     out = check_output(shlex.split(cmd))
