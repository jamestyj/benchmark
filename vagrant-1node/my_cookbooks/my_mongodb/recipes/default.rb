execute 'install_dstat_mongodb_plugin' do
  command 'wget -P /usr/share/dstat/ https://raw.github.com/gianpaj/dstat/master/plugins/dstat_mongodb_cmds.py'
  not_if { FileTest.directory?('/usr/share/dstat/dstat_mongodb_cmds.py') }
end

execute 'install_mongo_hacker' do
  command [ 'wget -P /tmp https://github.com/TylerBrock/mongo-hacker/archive/master.zip',
            'unzip /tmp/master.zip -d /tmp/',
            'cd /tmp/mongo-hacker-master',
            'make',
            'ln mongo_hacker.js /home/ec2-user/.mongorc.js',
            'chown ec2-user:    /home/ec2-user/.mongorc.js',
            'rm -rf /tmp/{mongo-hacker-master,master.zip}'
          ].join(' && ')
  not_if { ::File.exists?('/home/ec2-user/.mongorc.js') }
end

user_ulimit 'mongod' do
  filehandle_limit      64000
  filehandle_soft_limit 64000
  filehandle_hard_limit 64000
  process_limit         32000
end

execute 'chown mongod:mongod /data /journal /log'
execute 'ln -s /journal /data/journal'
