#!/bin/bash
function status_code(){
if [ $? -eq 0 ] ;
then
    echo "Success"
else 
    echo -e "\e[0;0;31;40m ============================= \e[0m"
    echo -e "\e[0;0;31;40m |   ERROR And Exit Script   | \e[0m"
    echo -e "\e[0;0;31;40m |   Please Check Up Log     | \e[0m"
    echo -e "\e[0;0;31;40m ============================= \e[0m"
    exit 0
fi
}
echo "=================================="
echo "|   Install Dependence Package   |"
echo "=================================="
sudo apt-get update  -y
sudo apt-get install libffi-dev libpq-dev libxml2-dev libxslt1-dev python-dev git python-pip  -y
sudo pip install virtualenv
status_code
# Install rally
echo "====================="
echo "|   Install rally   |"
echo "====================="
wget -q -O- https://raw.githubusercontent.com/openstack/rally/master/install_rally.sh | bash
status_code
# source admin
source /home/localadmin/creds/admin-openrc.sh
# cd to rally dir
cd rally/bin
# Registering an OpenStack deployment in Rally
echo "===================================================="
echo "|   Registering an OpenStack deployment in Rally   |"
echo "===================================================="
./rally deployment create --fromenv --name=iservcloud
status_code
# Verifying cloud via Tempest verifier
echo "============================================"
echo "|   Verifying cloud via Tempest verifier   |"
echo "============================================"
./rally verify create-verifier --type tempest --name tempest-verifier
status_code

echo "==================================================="
echo "|   Create external network and internal network  |"
echo "==================================================="
ext_ip=$(cat /home/localadmin/conf/tempest.conf | grep external_network_cidr | cut -d \= -f 2 |cut -d \   -f 2)
gateway=$(cat /home/localadmin/conf/tempest.conf | grep external_network_gateway | cut -d \= -f 2 |cut -d \  -f 2)
float_start=$(cat /home/localadmin/conf/tempest.conf | grep floating_ip_range_start | cut -d \= -f 2 |cut -d \   -f 2)
float_end=$(cat /home/localadmin/conf/tempest.conf | grep floating_ip_range_end | cut -d \= -f 2 |cut -d \   -f 2)
neutron net-create --shared --provider:physical_network provider \
  --provider:network_type flat ext-net

neutron subnet-create --name ext-net \
  --allocation-pool start=$float_start,end=$float_end \
  --dns-nameserver 8.8.8.8 --gateway $gateway \
  ext-net $ext_ip

neutron net-create selfservice

neutron subnet-create --name selfservice \
--dns-nameserver 8.8.4.4 --gateway 172.16.1.1 \
selfservice 172.16.1.0/24 
 
neutron net-update ext-net --router:external
neutron router-create router
  
neutron router-interface-add router selfservice
neutron router-gateway-set router ext-net
status_code

# Configure Tempest verifier
echo "=================================="
echo "|   Configure Tempest verifier   |"
echo "=================================="
./rally verify configure-verifier
status_code
# Configure tempest.conf
python /home/localadmin/set_tempest_conf.py
# Cp tempest.conf to rally dir
cp /home/localadmin/conf/tempest.conf /home/localadmin/.rally/verification/*/for-*/
rm -rf /home/localadmin/.rally/verification/*/repo
mv /home/localadmin/repo /home/localadmin/.rally/verification/*/
status_code
# Test start
echo "=================================="
echo "|        Test Compute            |"
echo "==================================" 
./rally verify start --pattern tempest.api.compute --tag compute
echo "=================================="
echo "|        Test image              |"
echo "=================================="
./rally verify start --pattern tempest.api.image --tag image
echo "=================================="
echo "|        Test network            |"
echo "=================================="
./rally verify start --pattern tempest.api.network --tag network
echo "=================================="
echo "|        Test volume             |"
echo "=================================="
./rally verify start --pattern tempest.api.volume --tag volume
# Generate report
echo "=================================="
echo "|        Generate report         |"
echo "=================================="
compute_UUID=$(./rally verify list | grep compute | cut -d \| -f 2)
image_UUID=$(./rally verify list | grep image | cut -d \| -f 2)
network_UUID=$(./rally verify list | grep network | cut -d \| -f 2)
volume_UUID=$(./rally verify list | grep volume | cut -d \| -f 2)
./rally verify report --uuid $compute_UUID $image_UUID $network_UUID $volume_UUID --type html --to /home/localadmin/test_report.html
sudo mv /home/localadmin/test_report.html /var/www/
ip=$(cat /home/localadmin/conf/allone_deploy.conf | grep ALL_HOST= | cut -d \= -f 2)
apache=$(cat /home/localadmin/conf/allone_deploy.conf | grep APACHE_HTTP= | cut -d \= -f 2)
count=$(echo "http://$ip:$apache/test_report.html"|wc -c)
for (( i=0; i<=${count}+10; i=i+1 ));
do
    printf  "="
done
echo ""
for (( j=0; j<=(${i}-18); j=j+1 ));
do
    if [ $j == 0 ];
    then
        printf "|"
    fi
    if [ $j == $(($((${i}-18))/2)) ];
    then
        printf "All Test Complete"
    fi
    printf  " "
    if [ $j == $(($((${i}-18))-2)) ];
    then
        printf "|"
    fi
done
echo ""
for (( j=0; j<=${i}; j=j+1 ));
do
    if [ $j == 0 ];
    then
        printf "|"
    fi
    printf  " "
    if [ $j == $((${i}-3)) ];
    then
        printf "|"
    fi
done
echo ""
for (( j=0; j<=(${i}-30); j=j+1 ));
do
    if [ $j == 0 ];
    then
        printf "|"
    fi
    if [ $j == $(($((${i}-30))/2)) ];
    then
        printf "You can view test report in :"
    fi
    printf  " "
    if [ $j == $(($((${i}-30))-2)) ];
    then
        printf "|"
    fi
done
echo ""
for (( j=0; j<=(${count}+10); j=j+1 ));
do
    if [ $j == 0 ];
    then
        printf "|"
    fi
    if [ $j == 5 ];
    then
        printf "http://$ip:$apache/test_report.html"
    fi
    printf " "
    if [ $j == 9 ];
    then
        printf "|"
    fi
done
echo ""
for (( i=0; i<=${count}+10; i=i+1 ));
do
    printf  "="
done
echo ""
#echo "==========================================="
#echo "|            All Test Complete            |"
#echo "|                                         |"
#echo "|      You can view test report in :      |"
#echo "| http://$ip:$apache/test_report.html     |"
#echo "==========================================="
