from __future__ import print_function
import ConfigParser
import subprocess

def get_exitcode_stdout_stderr(cmd):
    """
    Execute the external command and get its exitcode, stdout and stderr.
    """
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=None, shell=True)
    out = process.communicate()
    return out

def set_conf_value(section, key, value):
    config = ConfigParser.ConfigParser()
    config.read('/home/localadmin/conf/tempest.conf')  
    config.set(section, key, value)
    config.write(open('/home/localadmin/conf/tempest.conf', 'wb'))

def read_conf_file(file_location):
    '''
    read conf file
    Parameters:
        file_location, file complete route
    Returns:
        imageDetails: dict
    '''
    imageDetails = {}
    with open(file_location) as f:
        for line in f.readlines():
            if "#" not in line and "=" in line:
                imageDetails[line.split("=")[0].strip(
                    None)] = line.split("=")[1].strip(None)
    return imageDetails

#Compute section         
def set_image_ref(image_id_cmd):
    print("Setting image_ref .....")
    image_id = get_exitcode_stdout_stderr(image_id_cmd)
    set_conf_value("compute", "image_ref", image_id[0].rstrip())
 
def set_image_ref_alt(image_id_cmd):
    print("Setting image_ref_alt .....")
    image_id = get_exitcode_stdout_stderr(image_id_cmd)
    set_conf_value("compute", "image_ref_alt", image_id[0].rstrip())

def set_fixed_network_name(fixed_network_name_cmd):
    print("Setting fixed_network_name .....")
    fixed_network_name = get_exitcode_stdout_stderr(fixed_network_name_cmd)
    set_conf_value("compute", "fixed_network_name", fixed_network_name[0].strip())

def set_min_compute_nodes(min_compute_nodes_cmd):
    print("Setting min_compute_nodes .....")
    min_compute_nodes = get_exitcode_stdout_stderr(min_compute_nodes_cmd)
    set_conf_value("compute", "min_compute_nodes", min_compute_nodes[0].rstrip())

    
#Identity section
def set_uri_and_uri_v3(conf_file):
    print("Setting uri_and_uri_v3 .....")
    conf_value=read_conf_file(conf_file)
    keystone_url=conf_value['ALL_HOST']
    keystone_port=conf_value['KEYSTONE_PORT']
    uri = 'http://{0}:{1}/v2'.format(keystone_url,keystone_port)
    uriv3 = 'http://{0}:{1}/v3'.format(keystone_url,keystone_port)
    set_conf_value("identity", "uri", uri)
    set_conf_value("identity", "uri_v3", uriv3)

def set_default_domain_id(default_domain_id_cmd):
    print("Setting default_domain_id .....")
    default_domain_id = get_exitcode_stdout_stderr(default_domain_id_cmd)
    set_conf_value("identity", "default_domain_id", default_domain_id[0].strip())

#Network section
def set_public_network_id(public_network_id_cmd):
    print("Setting public_network_id .....")
    public_network_id = get_exitcode_stdout_stderr(public_network_id_cmd)
    set_conf_value("network", "public_network_id", public_network_id[0].strip())

def set_floating_network_name(floating_network_name_cmd):
    print("Setting floating_network_name .....")
    floating_network_name = get_exitcode_stdout_stderr(floating_network_name_cmd)
    set_conf_value("network", "floating_network_name", floating_network_name[0].strip())

#oslo_concurrency
def set_lock_path(verifier_id_cmd, deployment_id_cmd):
    print("Setting lock_path .....")
    verifier_id = get_exitcode_stdout_stderr(verifier_id_cmd)
    deployment_id = get_exitcode_stdout_stderr(deployment_id_cmd)
    lock_path = "/home/localadmin/.rally/verification/verifier-{0}/for-deployment-{1}/lock_files".format(str(verifier_id[0].strip()),str(deployment_id[0].strip()))
    set_conf_value("oslo_concurrency", "lock_path", lock_path)
    
#Volume section    
def set_storage_protocol(check_beckend_ceph_cmd):
    print("Setting storage_protocol .....")
    check_beckend_ceph = get_exitcode_stdout_stderr(check_beckend_ceph_cmd)
    if check_beckend_ceph[0] =="":
        set_conf_value("volume", "storage_protocol", "ISCSI")
    else:
        set_conf_value("volume", "storage_protocol", "ceph")

#volume-feature-enabled section
def set_multi_backend(cinder_volume_multi_backend_check_cmd):
    cinder_volume_multi_backend_check = get_exitcode_stdout_stderr(cinder_volume_multi_backend_check_cmd)
    if (int(cinder_volume_multi_backend_check[0].strip())) > 1 :
        set_conf_value("volume-feature-enabled", "multi_backend", "True")
    else:
        set_conf_value("volume-feature-enabled", "multi_backend", "False")
    
if __name__ == '__main__':
    tempest_conf = "/home/localadmin/conf/tempest.conf"
    conf_file = "/home/localadmin/conf/allone_deploy.conf"
    image_id_cmd = "openstack image list --property name=cirros-0.3.4-x86_64-disk -f value -c ID"
    image_id_ceph_cmd = "openstack image list --property name=cirros-ceph.img -f value -c ID"
    fixed_network_name_cmd = "openstack network list |grep ext-net |cut -d \| -f 3"
    default_domain_id_cmd = "openstack domain list |grep default |cut -d \| -f 2"
    min_compute_nodes_cmd = "openstack host list | grep compute | cut -d \| -f 2 | wc -l"
    public_network_id_cmd = "openstack network list |grep ext-net |cut -d \| -f 2"
    floating_network_name_cmd = "openstack network list |grep ext-net |cut -d \| -f 3"
    verifier_id_cmd = " /home/localadmin/rally/bin/rally verify list-verifiers |grep tempest |cut -d \| -f 2"
    deployment_id_cmd = "/home/localadmin/rally/bin/rally deployment list |grep iservcloud |cut -d \| -f 2"
    check_beckend_ceph_cmd = "sudo ceph health detail"
    cinder_volume_multi_backend_check_cmd = "cinder service-list | grep cinder-volume | grep up | cut -d \| -f 2 | wc -l"
    try:
        print('============================')
        print('|  Setting tempest config  |')
        print('============================')
        ceph_backend_img = get_exitcode_stdout_stderr(check_beckend_ceph_cmd)
        if ceph_backend_img[0] =="":
            set_image_ref(image_id_cmd)
            set_image_ref_alt(image_id_cmd)
        else:
            set_image_ref(image_id_ceph_cmd)
            set_image_ref_alt(image_id_ceph_cmd)            
        set_fixed_network_name(fixed_network_name_cmd)
        set_uri_and_uri_v3(conf_file)
        set_default_domain_id(default_domain_id_cmd)
        set_min_compute_nodes(min_compute_nodes_cmd)
        set_fixed_network_name(fixed_network_name_cmd)
        set_public_network_id(public_network_id_cmd)
        set_floating_network_name(floating_network_name_cmd)
        set_lock_path(verifier_id_cmd, deployment_id_cmd)
        set_storage_protocol(check_beckend_ceph_cmd)
        set_multi_backend(cinder_volume_multi_backend_check_cmd)
        print('===================================')
        print('|  Set tempest config successful  |')
        print('===================================')
    except Exception as e:
        print(str(e))

