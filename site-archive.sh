#!/bin/bash -xe

env

ssh -i /var/jenkins_home/.ssh/id_rsa jenkins_ac@stagingweb001.nmdev.us "sudo -E -P /home/jenkins_ac/scripts/current/site-archive-child.sh $SITE"
current_size=$(ssh -i /var/jenkins_home/.ssh/id_rsa jenkins_ac@stagingweb001.nmdev.us "du /tmp/$SITE.tar.gz" | awk {'print$1'})
current_available=`df | grep /dev/mapper | awk -F ' ' '{print $4}'`
current_buffer=500000
remaining=$(expr $current_available - $current_size)

if [ $remaining -gt $current_buffer ];then
  scp -i /var/jenkins_home/.ssh/id_rsa jenkins_ac@stagingweb001.nmdev.us:/tmp/$SITE.tar.gz .
  ssh -i /var/jenkins_home/.ssh/id_rsa jenkins_ac@stagingweb001.nmdev.us "rm -rf /tmp/$SITE.tar.gz"
else
  ssh -i /var/jenkins_home/.ssh/id_rsa jenkins_ac@stagingweb001.nmdev.us "rm -rf /tmp/$SITE.tar.gz"
  echo "Insufficient disk space on the jenkins host to take a drush archive-dump."
  exit 1
fi
