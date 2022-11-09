# -*- mode: ruby -*-
# vi: set ft=ruby :

# Specify minimum Vagrant version and Vagrant API version
Vagrant.require_version '>= 1.6.0'
VAGRANTFILE_API_VERSION = '2'

# Create and configure the VMs
Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  config.vm.network "public_network", bridge: "eth0"

  # Always use Vagrant's default insecure key
  config.ssh.insert_key = false

  # Mount source code directory
  config.vm.synced_folder ".", "/usr/src/secpi"

  config.vm.define "secpi-debian11" do |machine|

    # Don't check for box updates
    machine.vm.box_check_update = false

    # Specify the hostname of the VM
    machine.vm.hostname = "secpi-debian11"

    # Specify the Vagrant box to use
    machine.vm.box = "generic/debian11"
    #machine.vm.box = "debian/stretch64"
    #machine.vm.box = "ubuntu/bionic64"

    # Configure host specifications
    machine.vm.provider :virtualbox do |v|

      v.memory = 4096
      v.cpus = 4

      v.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]
      v.customize ["modifyvm", :id, "--name", "secpi-debian11"]
      #v.customize ["modifyvm", :id, "--memory", 4096]

    end

    machine.vm.provision :shell, inline: <<-SHELL
        echo "Installing required packages"
        set -x
        sudo apt-get update
		sudo apt-get upgrade
        sudo apt-get install --yes git python3-pip python3-venv rabbitmq-server amqp-tools mosquitto mosquitto-clients httpie socat mariadb-server asterisk ffmpeg

        # Git settings for `root`.
        sudo git config --global pull.ff only

        # Git settings for `vagrant`.
        su vagrant -c "git config --global pull.ff only"
    SHELL
	
	# Setup MariaDB
    machine.vm.provision :shell, privileged: true, inline: <<-SHELL
        #debconf-set-selections <<< "mysql-server mysql-server/root_password password secret"
		#debconf-set-selections <<< "mysql-server mysql-server/root_password_again password secret"

		mysql -e "CREATE DATABASE secpi;"
		mysql -e "grant all privileges on secpi.* TO 'secpi'@'localhost' identified by 'secret';"
		mysql -e "grant all privileges on secpi.* TO 'secpi'@'%' identified by 'secret';"
		
		mysql -e "CREATE DATABASE secpi-testdrive;"
		mysql -e "grant all privileges on secpi.* TO 'secpi-testdrive'@'localhost' identified by 'secret';"
		mysql -e "grant all privileges on secpi.* TO 'secpi-testdrive'@'%' identified by 'secret';"
    SHELL

    # Setup SecPi sandbox
    machine.vm.provision :shell, privileged: true, inline: <<-SHELL
        SOURCE=/usr/src/secpi
        TARGET=/opt/secpi

        echo "Installing package from ${SOURCE} to virtualenv at ${TARGET}"
        echo "Installing program to ${PROGRAM}"
        set -x
        whoami
        python3 -m venv ${TARGET}
        set +x
        source ${TARGET}/bin/activate
        set -x
        python -V

        # `setuptools 0.64.0` adds support for editable install hooks (PEP 660).
        # https://github.com/pypa/setuptools/blob/main/CHANGES.rst#v6400
        pip install "pip>=22" "setuptools>=64" --upgrade

        pip install --editable=${SOURCE}[test,develop] --upgrade
        ln -sf ${TARGET}/bin/secpi-* /usr/local/bin/
    SHELL

  end

end # Vagrant.configure
