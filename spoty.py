import json
import time
import os
import boto.ec2

from fabric.context_managers import settings
from fabric.api import *

# dict 
d_aws = {} 
# Enter your AWS credentials
d_aws['aws_secret'] = "INSERT_YOUR_KEY"
d_aws['aws_key'] = "INSERT_KEY_HERE"
d_aws['region'] = "us-west-2"
SLEEP_TIME = 5
env.key_filename = '/path/to/ec2instance.pem'
env.user = 'root'
env.hosts = []

def read_conf_file(distro):
	if distro == "ubuntu":
        	CONFIG_FILE_PATH = "/path/to/aws_config.json_ubuntu"
	else:
	        CONFIG_FILE_PATH = "/path/to/aws_config.json"

	# Load config from json file
	j_fd = open(CONFIG_FILE_PATH)
	config = json.load(j_fd)
	j_fd.close()
	return config


def ec2_connect():
	# Open EC2 connection
	ec2_conn = boto.ec2.connect_to_region(d_aws['region'],aws_access_key_id=d_aws['aws_key'],aws_secret_access_key=d_aws['aws_secret'])
        return ec2_conn


def req_instance_and_tag(ec2_conn,config):

	### BLOCK DEV INFO
	# Configure block device mapping
	if 'block-device-mapping' in config:
	    bdm = boto.ec2.blockdevicemapping.BlockDeviceMapping()
	    for name, bd in config['block-device-mapping'].iteritems():
		bdm[name] = boto.ec2.blockdevicemapping.BlockDeviceType(**bd)
	else:
	    bdm = None
	#### BLOCK DEV INFO ENDS

	# Request spot instance
	spot_req = ec2_conn.request_spot_instances(block_device_map=bdm,
						   **config['spot-request'])[0]

	# Tag the request, once we can get a valid request ID.
	print('Tagging spot request.')
	while True:
	    try:
		ec2_conn.create_tags(spot_req.id, config['tags'])
	    except:
		pass
	    else:
		break

	# Wait while the spot request remains open
	state = 'open'
	while state == 'open':
	    time.sleep(SLEEP_TIME)
	    spot = ec2_conn.get_all_spot_instance_requests(spot_req.id)[0]
	    state = spot.state
	    print('Spot request ' + spot.id + ' status: ' + spot.status.code + ': ' +
		  spot.status.message)

	# Exit if there is an error
	if (state != 'active'):
	    exit(1)
        return spot,bdm

def set_bdm(spot,bdm,ec2_conn,config):
	#################
	# Get the instance that was just launched, waiting until the number of block
	# devices attached to the instance is at least as many as requested.
	bd_count = 0
	ids_to_tag = []
	while bd_count < len(bdm):
	    time.sleep(4)
	    instance = ec2_conn.get_only_instances(spot.instance_id)[0]
	    bd_count = len(instance.block_device_mapping)

	# Get block devices to tag
	for bd in instance.block_device_mapping.itervalues():
	    ids_to_tag.append(bd.volume_id)
	# Tag resources
	print('Tagging instance and attached volumes.')
	ec2_conn.create_tags(ids_to_tag, config['tags'])

	##################

	instance = ec2_conn.get_only_instances(spot.instance_id)[0]
	# Wait till instance is out of pending state
	while instance.state == 'pending':
	    time.sleep(SLEEP_TIME)
	    instance = ec2_conn.get_only_instances(spot.instance_id)[0]
	    print('Instance ' + instance.id + ' state: ' + instance.state)
        return instance


def install_sw(instance,distro):
        ###  fab aetup
	env.hosts.append(instance.ip_address)
	if distro == "ubuntu":
		env.user="ubuntu"

        for x in range(50):
            try:
                with settings(host_string=env.user +'@'+ instance.ip_address):
	            run("sudo ls /tmp")
                    print "Uploading json files"
                    put("/home/laks/tmp/tutorials/"+str(instance.ip_address)+".json","/tmp/db.json")
                    run("mongo test --eval 'db.dropDatabase()'")
		    if env.user == "ubuntu":
     	        	  run('mongoimport -d test -c tutorials /tmp/db.json --jsonArray')
		    else:
	                  run('mongoimport -d test -c tutorials /tmp/db.json')
	            run("sudo ls /tmp")
		    #run('sudo rm -f /.ttyjs/ttyjs_telescope_setup/ttyjs2/app.js')
		    run ('sudo touch /root/'+str(instance.ip_address))
		    run ('sudo touch /root/style.css  /root/style.css_new ')
		    run ('sudo rm -rf /root/style.css  /root/style.css_new')
                    #run('rm -f /tmp/db.json')
		    #run('rm -f /.ttyjs/ttyjs_telescope_setup/ttyjs2/node_modules/tty.js/static/style.css')
		    #put('/home/laks/style.css','/.ttyjs/ttyjs_telescope_setup/ttyjs2/node_modules/tty.js/static/style.css')
		    #run ("sed -i 's/geometry:\ \[80,\ 24\]/geometry:\ \[80,\ 44\]/g' /.ttyjs/ttyjs_telescope_setup/ttyjs2/node_modules/tty.js/node_modules/term.js")
                    break
            except:
                time.sleep(3)
            else:
                 break 


	### fab ends
'''
	os.system("ssh -o StrictHostKeyChecking=no -i "+env.key_filename +" "+env.user+'@'+instance.ip_address+" 'sudo yum -y install screen' ")
	os.system("ssh -o StrictHostKeyChecking=no -i "+env.key_filename +" "+env.user+'@'+instance.ip_address+" 'sudo iptables -F' ")
	os.system("ssh -o StrictHostKeyChecking=no -i "+env.key_filename +" "+env.user+'@'+instance.ip_address+" 'screen -dm /usr/bin/node /home/fedora/node_modules/tty.js/bin/tty.js' ")
'''

def del_sys(instance,ec2_conn):
	print("Deleting instance in  which as has ip:" + str(instance.id) + str(instance.ip_address))
	ec2_conn.terminate_instances(instance.id)

	print "Delete Free volumes" 
	my_all_vol=ec2_conn.get_all_volumes()
	for v in my_all_vol:
	     print v.id
	     print v.status
	     if v.status == "available":
		   print ("Deleting Volume" + v.id)  
		   ec2_conn.delete_volume(v.id)

## Call functions
'''
ec2_conn=ec2_connect()
spot,bdm = req_instance_and_tag(ec2_conn)
instance=set_bdm(spot,bdm,ec2_conn)
install_sw(instance)
del_sys(instance,ec2_conn)
'''
