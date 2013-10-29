# For import_to_mongo.py
package 'gcc'
package 'git'
package 'python-devel'
package 'python-pip'

python_pip 'pymongo'
python_pip 'pylru'

execute 'git_clone_benchmark' do
  command [ 'cd /home/ec2-user',
            'git clone https://github.com/jamestyj/benchmark.git',
            'chown -R ec2-user: /home/ec2-user/benchmark'
          ].join(' && ')
  not_if { FileTest.directory?('/home/ec2-user/benchmark') }
end

template '/home/ec2-user/.bashrc' do
  source 'bashrc.erb'
  owner  'ec2-user'
  group  'ec2-user'
  variables({
    :region     => 'us-east-1',
    :access_key => node[:ebs][:access_key],
    :secret_key => node[:ebs][:secret_key]
  })
end
