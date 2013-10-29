# Install the following packages
package 'htop'     # CPU and memory statistics
package 'dstat'    # CPU, memory, network, and disk statistics
package 'sysstat'  # Disk (iostat) and other system statistics
package 'tree'     # View directory structure
package 'tmux'     # Better than 'screen'

# Update the system
execute 'yum -y update'

# Clean up leftovers from vagrant-omnibus
execute 'rm -f /home/ec2-user/install.sh'
