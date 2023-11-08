# For host admins 

Host admins have root access to the host machine.
They are responsible for everything, especially for security.

In this chapter, we sketch how to set up a (hopefully) secure host publicly accessibly from the outside world, and we provide information on maintenance tasks, general ones and JupyterHub related ones.

```{contents}
---
local: true
---
```

## Installing the host system

```{warning}
Setting up a publically accessible server is highly nontrivial.
It's a job for an experienced administrator.
The Ananke project team at the moment does not have an experienced administrator (just some mathematicians and other scientists).
Instructions written down below may contain rookie mistakes and potentially may harm your machine and your network! Ensure that you understand every single step you go and be aware of the consequences.
```

Considerations and steps described here by no means cover all relevant situations and settings.
They originate from setting up a public test system for the Ananke project and, thus, focus on hardware and network features available to the project team during time of development.

We assume that the reader has basic Linux administration and network knowledge.

A special feature of the installation instruction here is that we do not use services of the surrounding network (likely an educational institution's network), except for internet connectivity.
Reasons:
* The host machine may be moved to another network easily.
* There will be no or only minimal interference with central security measures like surveillance and antivirus tools.

Major sources for the instructions here are:
* [Debian GNU/Linux Installation Guide](https://www.debian.org/releases/bookworm/amd64/)
* [The Debian Administrator's Handbook](https://www.debian.org/doc/manuals/debian-handbook/index.en.html)
* [Securing Debian Manual](https://www.debian.org/doc/manuals/securing-debian-manual/index.en.html)

### Cross-install Debian

Ananke uses [Debian](https://www.debian.org/) for container images.
The host machine may use a different Linux flavor, but here we go with Debian, too.

We do not use the usual [Debian installer](https://www.debian.org/devel/debian-installer/) but manual installation for two reasons:
* We want to have a minimal installation.
* So we can be sure we control and understand the details.
* The host machine is likely to already serve a JupyterHub or something else, and we want to minimize downtime.

The approach we follow is known as cross-installation.
That is, we install a new operating system in parallel to the existing one.
After finishing the basic installation, we reboot the machine into the new system and remove the old one.

The [Debian Installation Guide](https://www.debian.org/releases/stable/amd64/) has a [section on cross-installation](https://www.debian.org/releases/stable/amd64/apds03.en.html) and there are a small number of tutorials, too.
See [How to install Debian from Debian](https://readme.phys.ethz.ch/documentation/how_to_install_debian_from_debian/), for instance.

Installation procedure has been tested with the following systems:
* Debian 12 for the new system, Ubuntu 22.04 LTS for the old one
* Debian 11 for the new system and for the old one (minor modifications are in order).

#### Prerequisites

We assume that the host is Linux-based and has internet access.
We have root access to the machine at least via SSH.
Physical access may avoid headaches, but is not necessary.

For cross-installation, we need unused disk space.
Here *unused* means that there is some space on a disk not belonging to a partition.
If you do not have enough unused space for a basic Linux installation (about 10 GB) try to shrink a file system and corresponding partition.
We do not cover the details here.

If you start with a fresh host machine (no operating system), install a standard Debian and leave some disk space unpartitioned.
Then follow the instructions below.

#### Disk partitioning

For partition management, we use logical volume management (LVM).
See [Debian Handbook](https://debian-handbook.info/browse/stable/advanced-administration.html#sect.lvm) and [Debian Wiki](https://wiki.debian.org/LVM) for relevant information.
LVM allows resizing and moving partitions without formatting them.
We will use this feature after removing the original system to make the whole disk available to the new one.

If not already available on your system, install LVM tools via
```
sudo apt install lvm2
```

Check available disks and their partition scheme with
```
sudo fdisk -l
```
You should also look at the output of
```
sudo cat /etc/fstab
sudo ls -la /dev/disk/by-uuid/
```
to see which partitions currently are in use.

If there is no unused partition, but unpartitioned disk space, create a new partition in unpartitioned area:
```
sudo fdisk /dev/nvme0n1
```
where `nvme0n1` has to be replaced by your disk's name.
Follow the interactive partitioning process by pressing/choosing `p`, `n`, `3`, `default`, `default`, `w` (maybe different for your situation!).

Now that we have an empty partition, we create a physical LVM volume in it:
```
sudo pvcreate /dev/nvme0n1p3
```
where `nvme0n1pe` is your new partitions name (check partition names with `sudo fdisk -l`).
With
```
sudo pvdisplay
```
we get a list of all physical LVM volumes.

Now we create a volume group `vg_main`:
```
sudo vgcreate vg_main /dev/nvme0n1p3
```
Display results:
```
sudo vgdisplay
```
Next, the logical volumes:
```
sudo lvcreate -n lv_root -L 50G vg_main
sudo lvcreate -n lv_var -L 10G vg_main
sudo lvcreate -n lv_tmp -L 10G vg_main
sudo lvcreate -n lv_home -L 100G vg_main
sudo lvcreate -n lv_swap -L 8G vg_main

sudo lvdisplay
```
See [Debian Installation Guide](https://www.debian.org/releases/stable/amd64/apcs03.en.html) for hints on how many partitions to use and on partition sizes.

Format all partitions:
```
sudo mkfs.ext4 /dev/vg_main/lv_root
sudo mkfs.ext4 /dev/vg_main/lv_var
sudo mkfs.ext4 /dev/vg_main/lv_tmp
sudo mkfs.ext4 /dev/vg_main/lv_home

sudo mkswap /dev/vg_main/lv_swap

sudo sync
```

(debootstrap)=
#### Debootstrap

The Debian ecosystem provides `debootstrap` for minimal manual installations.
Install with
```
sudo apt install debootstrap
```

Before we run `debootstrap` we have to mount the file systems for the new system:
```
sudo  mkdir /mnt/debinst
sudo  mount /dev/vg_main/lv_root /mnt/debinst

sudo  mkdir /mnt/debinst/var
sudo  mount /dev/vg_main/lv_var /mnt/debinst/var

sudo  mkdir /mnt/debinst/tmp
sudo  mount /dev/vg_main/lv_tmp /mnt/debinst/tmp

sudo  mkdir /mnt/debinst/home
sudo  mount /dev/vg_main/lv_home /mnt/debinst/home

sudo swapon /dev/vg_main/lv_swap
```
Now run
```
sudo debootstrap --arch amd64 --verbose stable /mnt/debinst http://ftp.tu-chemnitz.de/debian
```
You may specify different architecture (`amd64`), different version (`stable`) and different mirror (`http://ftp.tu-chemnitz.de/debian`).

(chroot-into-the-new-system)=
#### Chroot into the new system

We use [`chroot`](https://wiki.debian.org/chroot) to proceed with the installation process until the new system is bootable and provides SSH access.

To enter the `chroot` environment first **mount all file systems** (see [debootstrap](#debootstrap)) and then run
```
sudo LANG=C.UTF-8 chroot /mnt/debinst /bin/bash
```
The console now lives inside the new system.
Run
```
mount none /proc -t proc
chmod 777 /tmp
```
inside `chroot` to make several important things work.

To leave the `chroot` environment type
```
exit
```

Almost all steps described below have to be done in the `chroot` environment.

#### Basic config files

We have to create basic config files for the new system.
[Enter the `chroot` environment](#chroot-into-the-new-system) for the following steps.

We start with the file systems to mount on boot.
Write the following to `/etc/fstab`:
```
# /etc/fstab: static file system information.
#
# file system          mount point   type    options                  dump pass
/dev/vg_main/lv_root   /             ext4    defaults                 0    1
/dev/vg_main/lv_tmp    /tmp          ext4    rw,nosuid,nodev          0    2
/dev/vg_main/lv_var    /var          ext4    rw,nosuid,nodev          0    2
/dev/vg_main/lv_home   /home         ext4    rw,nosuid,nodev          0    2

/dev/vg_main/lv_swap   none          swap    sw                       0    0
/dev/nvme0n1p1         /boot/efi     vfat    umask=0077               0    1
```
One of many ways to do this is
```
nano /etc/fstab
```
Save and close with `Ctrl+x`, `y`, `return`.
Replace `nvme0n1p1` by the name of your EFI partition, if you have an EFI system.
For BIOS systems, remove that line.

Initialize timer correction by creating `/etc/adjtime` with content
```
0.0 0 0.0
0
UTC
```
Then run
```
dpkg-reconfigure tzdata
```

To make the `apt` package manager work place the following in `/etc/apt/sources.list`:
```
deb http://ftp.tu-chemnitz.de/debian bookworm main contrib non-free-firmware
deb-src http://ftp.tu-chemnitz.de/debian bookworm main contrib non-free-firmware

deb http://security.debian.org/ bookworm-security main contrib non-free-firmware
deb-src http://security.debian.org/ bookworm-security main contrib non-free-firmware
```
(replace the mirror `http://ftp.tu-chemnitz.de` if it is not close to your location).
Then reload package information via
```
apt update
```

For network management we use `systemd`.
Create `/etc/systemd/network/50-ether-static.network` with content
```
[Match]
Name = enp1s0

[Network]
Address = 192.168.178.53/24
Gateway = 192.168.178.1
DNS = 192.168.178.1
DNS = 8.8.8.8
DNS = 8.8.4.4
Domains = ~.
```
Replace all values with your network information.
**On the host system** (not in `chroot`) run
```
ip -c route get 1.1.1.1
```
to get the name of the network interface used for internet connectivity.
A list of all network interfaces is shown by
```
ip addr show
```
If your host system manages network with NetworkManage, run
```
nmcli device show enp1s0
```
(where `enp1s0` has to be replaced by the correct interface) to get relevant information.
If the host system uses `systemd` for network management have a look at the files in `/etc/systemd/network`.

Enable `systemd` network management **in the `chroot` environment** via
```
systemctl enable systemd-networkd.service
```
For DNS, you may use your networks DNS server or public DNS servers provided by Google (8.8.8.8, 8.8.4.4) or Cloudflare (1.1.1.1) or others.
Beware of the fact that DNS server providers see all the servers you communicate with and how often and at what time you communicate with another machine!

Create `/etc/hosts` with content
```
127.0.0.1       localhost
127.0.1.1       your_hostname
```
with `your_hostname` suitably replaced (run `hostname` on a host system to get your hostname).

```{important}
The setup described here is for IPv4 networks.
If your machine lives in a IPv6 network things (IP addresses!) will look different.
```

#### Additional packages and their configuration

It's time to install some packages **into the `chroot` environment** not belonging to the minimal installation done by `debootstrap`.

Choose and install a suitable Linux kernel via
```
apt search linux-image

apt install linux-image-amd64
```
(replace `amd64` with you machine's architecture).
Warnings about local problems and errors related to logging should be ignored at this point.
We'll solve this later on.

Some important tools:
```
apt install lvm2 sudo ssh systemd-resolved
```

Sometimes the ssh server `sshd` does not start properly at system boot due to improper configuration of the start-up process of `systemd`To ensure `sshd` comes up without problems create the file (and corresponding directories) `/etc/systemd/system/sshd.service.d/wait.conf` with content
```
[Unit]
Wants=network-online.target
After=network-online.target
```

#### User account

The new system needs a user account\nWe adhere to the `sudo` variant, that is, there will be no root user.
**In the `chroot` environment** create a user via
```
adduser some_username
```
This will be the admin account.
Some people say that we shouldn't call an admin's account `admin` to make it harder for attackers to find the account to attack.
Choose a really secure password!

Then allow `sudo` for the account:
```
usermod -a -G sudo your_username
```

(bootloader-grub-configuration)=
#### Bootloader (GRUB) configuration

Bootloader configuration has to be done **on the host system** (not in `chroot`).
After booting into the new system, we'll install GRUB there and hand the boot process over to the new system.

```{warning}
Be careful here: mistakes may render your systems (old and new) unbootable! GRUB configuration heavily depends on your overall setup and also on your hardware.
Check every detail twice!
```

Edit `/etc/default/grub`:
* Set `GRUB_TIMEOUT` to something greater than zero to allow for manual OS selection on boot.
* This is only relevant with physical access to the machine and if something goes wrong during reboot.
* Add a line with `GRUB_DISABLE_OS_PROBER=false`.
* This tells GRUB to autodetect operating systems (now you have at least two on your machine).

Run
```
sudo update-grub
```

````{important}
Read the output of `update-grub`.
If it tells you that `os-prober` won't be executed, then something went wrong.
We need `os-prober`.
Perhaps there is some GRUB config file overwriting our choice `GRUB_DISABLE_OS_PROBER=false`.
Run
```
sudo grep -r "GRUB_DISABLE_OS_PROBER" /etc/
```
to find such config files.
Then change settings there.
````

In principle, we could reboot now into the new system.
But, especially if we don't have physical access to the system, we have to tell GRUB which OS to boot.
Have a look at `/boot/grub/grub.cfg`.
There are lines starting with `menuentry` and maybe also with `submenu`.
Either get the title of the new system's entry or get its number.
Counting starts at 0 and a whole `submenu` block counts like one `menuentry`.
Run
```
sudo grub-reboot menu_entry_title_or_number
```
make GRUB boot the new system at next reboot.
If you need to boot a submenu item, specify it as `submenu_title_or_number>submenu_entry_title_or_number`.
See [manpage of `grub-reboot`](https://manpages.debian.org/bookworm/grub2-common/grub-reboot.8.en.html), too.

#### Reboot into the new system

Run
```
sudo reboot now
```
and login with your admin account created above.
SSH should work, so you shouldn't need physical access to the machine.

#### Check network configuration

Check network status with
```
networkctl list
networkctl status
networkctl status --all
```

#### Some fine-tuning

The `apt` package manager should work now.
Let's update installed packages:
```
sudo apt update
sudo apt upgrade
```

Configure locales and keyboard:
```
sudo apt install locales console-setup

sudo dpkg-reconfigure locales
sudo dpkg-reconfigure keyboard-configuration

sudo systemctl restart console-setup.service
```

Have a look at the kernel logs:
```
sudo dmesg
```
If there are complaints about missing firmware, install `apt-file` via
```
sudo apt install apt-file
sudo apt-file update
```
and look for the package containing the missing files:
```
apt-file search name_of_missing_firmware_file
```

Install help systems:
```
sudo apt install man info
```

Disable automatic updates (optional, don't forget to do them manually at least weekly):
```
sudo systemctl disable apt-daily.timer
sudo systemctl disable apt-daily-upgrade.timer
```

Remove `debootstrap` logs:
```
sudo rm /var/log/bootstrap.log
```

To guarantee logging to disk, in `/etc/systemd/journald.conf` change `Storage=auto` to `Storage=persistent`.
Then restart logging with
```
sudo systemctl restart systemd-journald
```

Install time synchronization via NTP:
```
sudo apt install systemd-timesyncd
```

#### Install GRUB

It remains to install GRUB on the new system.

```{warning}
Be careful here: mistakes may render your systems (old and new) unbootable! GRUB configuration heavily depends on your overall setup and also on your hardware.
Check every detail twice!
```

Run
```
sudo apt install grub-efi
```
or
```
sudo apt install grub-pc
```
depending on your machine's boot procedure to install GRUB packages.

Then install GRUB to the partition already used by the old system for GRUB (the one mounted to `/boot/efi` in old system's `/etc/fstab`):
```
sudo grub-install /dev/nvme0n1
```

Edit `/etc/default/grub` following the description in [bootloader (GRUB) configuration](#bootloader-grub-configuration), but now on the new system, and run
```
sudo update-grub
```

Finally, set GRUB's default menu entry to boot via
```
sudo grub-set-default menu_entry_title_or_number_of_new
```

If you want to boot into the old system, run
```
sudo grub-reboot menu_entry_title_or_number_of_old
```

Test the GRUB installation with
```
sudo reboot now
```

#### Removing the old system

The new system should work now, but it's a good idea to keep the old one until you are really sure that the new one works flawlessly.

To remove the old system, we take its disks partitions and add them the new systems `home` partition.
Thus, entire disk space will be available to the new system.

Find the old system's partitions from the output of
```
sudo fdisk -l
sudo pvdisplay
```
(partitions displayed by `fdisk` but not by `pvdisplay` belong the old system, up to the EFI partition on EFI systems).

Have a look at the output of
```
sudo vgdisplay
sudo lvdisplay
```
to find the `home` partitions logical volume (`/dev/vg_main/lv_home` if you followed instructions above).
Then create a physical volume:
```
sudo pvcreate /dev/nvme0n1p2
```
(replace `nvme0n1p2` by your partition name).
Add the new physical volume to the volume group `vg_main` via
```
sudo vgextend vg_main /dev/nvme0n1p2
```
and extend the `home` volume to fill all available space:
```
sudo lvextend -l +100%FREE /dev/vg_main/lv_home
```
Finally, extend the file system to fill the whole volume:
```
sudo resize2fs /dev/vg_main/lv_home
```

### E-Mail notifications

We would like to receive an email if something important happens on the server.
Daily or weekly usage reports via email are a good idea, too.

To make email notifications work, we need a world-facing SMTP server.
Setting one up on our host machine is not trivial and should be avoided (usually all mails coming from 'small' SMTP servers are classified as spam).
A better idea is to use an external SMTP server (a free mailer or your institutions' mail server).

```{important}
Don't use your standard mail account (at your institution, for instance) for sending because we have to store credentials on our server.
Although only admin users have access to the credentials file, it's not a good idea.
Better create a new mail account solely used for sending notifications from our server to the outside world.
```

Here we use the small and simple [DragonFly Mail Agent (dma)](https://github.com/corecode/dma).
Install:
```
sudo apt install dma
```
For *system mail name* use your machine's hostname and domain name (`host.domain.org`).
Leave the *smarthost* field blank.

Install standard tools for mail management (send mail to other users aso.):
```
sudo apt install mailutils
```

To configure `dma` modify `/etc/dma/dma.conf` as follows
```
SMARTHOST your_mail_accounts_smtp_server
PORT your_mail_accounts_smtp_port
AUTHPATH /etc/dma/auth.conf
SECURETRANSFER
MAILNAME /etc/mailname
MASQUERADE your_mail_accounts_mail_address
```
Comment all other lines.
Now write your credentials to `/etc/dma/auth.conf`:
```
your_mail_accounts_username|your_mail_accounts_smtp_server:your_mail_accounts_password
```

All emails sent from root or your admin user shall be forwarded to your standard (institutional) email account.
Emails generated by other accounts shall be ignored.
Modify `/etc/aliases` as follows
```
root: your_username
your_username: where.to.send@notifications.to
*: mail_trash_user
```
Then run
```
sudo newaliases
```

We may remove the admin user's local inbox if it has been created:
```
rm /var/spool/mail/your_username
```
To prevent other users (container admins) from sending mails run
```
sudo chmod o-rwx /sbin/dma
```
and add your admin user to the `mail` group:
```
sudo adduser your_username mail
```
Logout and login to activate the new group membership.

### Hardening the system

Now that the basic installation is finished, we should make it more secure.
That's the difficult part.
Consider the following steps as suggestions.
Some may be appropriate for your setting, some not.
Some may be missing, some may be considered overly paranoid.

#### Unused network services

If you are in an IPv4 network, you may disable all the IPv6 stuff.
There are several possibilities to accomplish this, but the simplest and most trustworthy one is to set a kernel option.
Edit following lines in `/etc/default/grub`:
```
GRUB_CMDLINE_LINUX_DEFAULT="ipv6.disable=1 quiet"
GRUB_CMDLINE_LINUX="ipv6.disable=1"
```
Then
```
sudo update-grub
sudo reboot
```

In some settings, it may be appropriate to disable LLMNR.
To `/etc/systemd/resolved.conf` add the line
```
LLMNR=no
```
Then
```
sudo systemctl restart systemd-resolved
```

To list all open TCP and UDP ports, run
```
ss -tulpan
```

#### SSH and Fail2ban

We use a simple form of two-factor authentication: password and cryptographic key.

```{important}
When modifying SSH config always keep one connection open until the new config works.
Else you may get locked out from your machine.
```

The following `/etc/ssh/sshd_config` file is rather restrictive:
```
Include /etc/ssh/sshd_config.d/*.conf

Port 986
AddressFamily inet
ListenAddress 123.456.789.012

PermitRootLogin no
PasswordAuthentication no
ChallengeResponseAuthentication yes
AuthenticationMethods publickey,keyboard-interactive
UsePAM yes

LoginGraceTime 1m
X11Forwarding no
PrintMotd no
AcceptEnv LANG LC_*

Subsystem sftp /usr/lib/openssh/sftp-server

AllowUsers your_username
```
Choose a non-standard port for SSH to get invisible to attackers scanning only for port 22.
The `ListenAddress` is the IP address of the host's network interface used for internet connectivity.
Only SSH connections coming in via that IP address are allowed.
See [`sshd_config` man page](https://manpages.debian.org/bookworm/openssh-server/sshd_config.5.en.html) for details.

For crypto key authentication, your admin user has to provide a public key:
```
cd ~
mkdir .ssh
chmod 700 .ssh
cd .ssh
touch authorized_keys
chmod 600 authorized_keys
```
Place the public key in `authorized_keys` file.
On a Linux machine a user's standard public key is in `~/.ssh/id_rsa.pub`.
If you do not have a key pair on your client machine (the one used to SSH into the server), create one with
```
ssh-keygen
```

Now restart `sshd`:
```
sudo systemctl restart sshd.service
```

To prevent brute-force attacks, install and enable ['Fail2ban'](https://www.fail2ban.org):
```
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

Place the following in `/etc/fail2ban/jail.local`:
```
[DEFAULT]
destemail = where.to.send@notifications.to
sender = your_mail_accounts_mail_address
sendername = Fail2ban
banaction = nftables-multiport
banaction_allports = nftables-allports
action = %(action_mwl)s

[sshd]
enabled = false

[sshd-aggressive]
enabled = true
filter = sshd[mode=aggressive]
port = ssh
backend = systemd
journalmatch = _SYSTEMD_UNIT=sshd
action = %(action_mw)s
```
Then
```
sudo systemctl restart fail2ban
```

Fail2ban allows only for a limited number of failed login attempts (default: 3 attempts in 10 minutes).
IP addresses with to many attempts are blocked for a certain time (default: 10 minutes) via temporary firewall rules and an email is sent to you.
To list all currently blocked IP addresses run
```
sudo fail2ban-client status sshd-aggressive
```
To unban an IP address, manually run
```
sudo fail2ban-client set sshd-aggressive unbanip 123.456.789.012
```

#### Firewall

Debian's standard firewall is [`nftables`](https://nftables.org/projects/nftables/index.html).
To enable it run
```
sudo systemctl enable nftables.service
sudo systemctl start nftables.service
```
Currently active filter rules are shown with
```
sudo nft list ruleset
```

Create the file `/etc/nftables.conf` with content
```
#!/usr/sbin/nft -f

flush ruleset

table ip filter {
    chain in_ipv4 {
        type filter hook input priority 0; policy drop;
        ct state vmap { established : accept, related : accept, invalid : drop }
        iifname lo accept
        icmp type echo-request limit rate 5/second accept
        tcp dport 986 accept
        log prefix "[nftables] Inbound Denied: " counter drop
    }
    chain for_ipv4 {
        type filter hook forward priority 0; policy drop;
    }
    chain out_ipv4 {
        type filter hook output priority 0; policy accept;
    }
}
``` 
and run
```
sudo nft -f /etc/nftables.conf
```
to get a rather restrictive firewall (only outgoing connections and SSH allowed, limited ICMP echos).

Configuration details can be found in the [`nftables wiki`](https://wiki.nftables.org).

#### Log reports

We would like to get daily log summaries via email.
This can be done with `logwatch`.
Install
```
sudo apt install logwatch net-tools
```
and create `/etc/logwatch/conf/logwatch.conf` with content
```
Detail = 5
Service = All
```

Then create a dummy log file `/var/log/logwatch_journald.log` with arbitrary content (not empty!):
```
This file exists to make logwatch work with journald.
Logwatch wants to have some log file, but messages to process will come from journalctl.
```

Create the file `/etc/logwatch/conf/logfiles/journald.conf` with content
```
LogFile = logwatch_journald.log
```
and a file `/etc/logwatch/conf/services/journald.conf` with content
```
LogFile =
LogFile = journald
*JournalCtl = "--output=cat"
Title = "journald messages"
```
We also need a file `/etc/logwatch/scripts/services/journald` with content
```
#!/usr/bin/bash
egrep 'error|warning|critical'
```
This must be executable:
```
sudo chmod a+x /etc/logwatch/scripts/services/journald
```

Logwatch will send a daily report to the root user (which will be forwarded to your mail account).
Time for daily tasks can be adjusted in `/etc/crontab`.

#### Restrict file access

Debian's standard file access permission should be tightened somewhat.
Access rights for newly created files usually are 755 (or 644).
We change this to 750 (or 640).
Then only the file's owner has full access, and its group has read access.
This prevents users from looking into `home` directories of other users.
For this purpose create a file `/etc/profile.d/umask.sh` with content
```
umask 027
```
Set access rights for new `home` directories accordingly by editing `/etc/adduser.conf`:
```
DIR_MODE=0750
```
and running
```
sudo chmod -R o-rwx /etc/skel
```
For already existing `home` directories we have to adjust access manually:
```
sudo chmod -R o-rwx /root
sudo chmod -R o-rwx /home/your_username
```

Finally, we adjust access to some config files:
```
sudo chmod o-rwx /etc/sudoers.d

sudo chmod o-rwx /etc/ssh/sshd_config
sudo chmod o-rwx /etc/ssh/sshd_config.d

sudo chmod -R o-rwx /etc/cron.d
sudo chmod -R o-rwx /etc/cron.daily
sudo chmod -R o-rwx /etc/cron.hourly
sudo chmod -R o-rwx /etc/cron.monthly

sudo chmod o-rwx /etc/crontab
```

#### Unused kernel modules

Debian's Linux kernel ships with some kernel modules for network services we do not need.
Thus, we should deactivate them.
Simply add some lines to `/etc/modprobe.d/blacklist.conf`:
```
install dccp /bin/true
install sctp /bin/true
install rds /bin/true
install tipc /bin/true
```

#### Core dumps

Core dumps are used for debugging programs, but may also be used by attackers to obtain system information.
We should prevent the kernel from automatically generating core dumps if something went wrong.
Create `/etc/sysctl.d/50-coredump.conf` with content
```
kernel.core_pattern=/dev/null
```
and then run
```
sudo sysctl -p /etc/sysctl.d/50-coredump.conf
```
To `/etc/security/limits.conf` add the line
```
* hard core 0
```

#### Malware and vulnerability detection

We should install some tools for detecting malware and unexpected modifications of the system.

To scan for rootkits install `rkhunter` and `chkrootkit`:
```
sudo apt install chkrootkit rkhunter
```
Test them with
```
sudo rkhunter --check
sudo chkrootkit
```

[`Tripwire`](https://github.com/Tripwire/tripwire-open-source) looks for modifications of important files and reports them.
Install with
```
sudo apt install tripwire
```
and answer both questions with 'No'.
Tripwire requires two keys for encrypting its configuration and database.
Create them with
```
sudo twadmin --generate-keys -L /etc/tripwire/YOUR_HOSTNAME-local.key
sudo twadmin --generate-keys -S /etc/tripwire/site.key
```
and remember both passwords.
Then create two config files via
```
sudo twadmin --create-cfgfile -S /etc/tripwire/site.key /etc/tripwire/twcfg.txt
sudo twadmin --create-polfile -S /etc/tripwire/site.key /etc/tripwire/twpol.txt
```
and edit the file `/etc/tripwire/twpol.txt` to meet your needs (run Tripwire as described below and look for errors due to non-existing files, then comment corresponding lines in the config file and run the `--create-polfile` line again).

Now tell Tripwire that the current file system state is correct and future states should be compared to the current state:
```
sudo tripwire --init
```

Test run Tripwire with
```
cd ~
sudo tripwire --check -r report.twr
```
If Tripwire found modified files and modifications are okay (!), add modifications to the Tripwire database:
```
sudo tripwire --update -a -r report.twr
```

Vulnerable Debian packages can be found with [`debsecan`](https://wiki.debian.org/DebianSecurity/debsecan).
Install:
```
sudo apt install debsecan
```
Run it with
```
sudo debsecan --suite bookworm --format report
```
to see all vulnerabilities.
Add the `--only-fixed` argument to see only vulnerabilities fixable by updating corresponding packages.

[Lynis](https://cisofy.com/lynis/) scans the system for all kinds of standard security problems and suggests solutions.
Install with
```
sudo apt install lynis
```
Run with
```
sudo lynis audit system
```

The [`debsums`](https://manpages.debian.org/bookworm/debsums/debsums.1.en.html) tool looks for modifications of files from installed packages.
Install with
```
sudo apt install debsums
```
Run
```
sudo debsums -ca
```
to get a list of files modified since installation of the corresponding package.

Install
```
sudo apt install apt-listbugs apt-listchanges
```
to automatically get a list of bugs and changes for packages you install with `apt`.

With
```
sudo apt install needrestart
```
you get information about the required reboot after each package installation.

#### System monitoring

We would like to gather statistics on who did what on our machine.
If we are facing problems, we may find the source more easily.
In addition, we have to keep an eye on network and CPU load to know when to go shopping for a better machine.
In this section, we install several tools for system monitoring and reporting.

User activity can be monitored with the [GNU Accounting Utilities](https://www.gnu.org/software/acct/).
Install:
```
sudo apt install acct
sudo accton on
```
To get user connect time statistics, commands executed, and a summary run
```
sudo ac
sudo lastcomm
sudo sa
```
See [GNU Accounting Utilities documentation](https://www.gnu.org/software/acct/manual/accounting.html) for details.

Performance monitoring tools are provided by the [`sysstat` package](https://packages.debian.org/bookworm/sysstat).
Install:
```
sudo apt install sysstat
sudo systemctl start sysstat
sudo systemctl enable sysstat
```
For general statistics run
```
sudo sar
sudo iostat
```
See [`sysstat` project page](https://github.com/sysstat) for details.

The Linux Auditing System (`auditd`) records all kinds of events on the system (e.g., syscalls).
It's quite useful for incident analysis.
Install:
```
sudo apt install auditd audispd-plugins
sudo systemctl start auditd
sudo systemctl enable auditd
```
The file `/etc/audit/rules.d/audit.rules` controls what to log.
We may use [one-size-fits-all `audit.rules`](https://github.com/Neo23x0/auditd) until we feel the need for more individual auditing rules.
After modifying that file run
```
sudo systemctl restart auditd
```

Logs are written to `/var/log/audit/audit.log` and may be inspected with [`ausearch`](https://man7.org/linux/man-pages/man8/ausearch.8.html) and [`aureport`](https://man7.org/linux/man-pages/man8/aureport.8.html).

### Reverse proxy

The host machine will provide (next to SSH) only one service to the outside world: an HTTP server.
This server takes incoming requests and forwards them to the correct Podman container.
Which container to forward to is determined by the request's URL.
Here we use [`nginx`](https://www.nginx.com/) as HTTP server.

Connection between the world and HTTP server will be encrypted (HTTPS).
Connection to containers won't be encrypted because traffic does leave the machine.

Install `nginx`:
```
sudo apt install nginx
```
Then tell the firewall to accept incoming requests on ports 80 (HTTP) and 443 (HTTPS): in `/etc/nftables.conf` replace your SSH port (e.g., 986) by `{986, 80, 443}` ad run
```
sudo nft -f /etc/nftables.conf
```
to reload firewall rules.

To improve security, we disable some `nginx` modules enabled by default:
```
cd /etc/nginx/modules-enabled
sudo rm -r *
sudo systemctl restart nginx
```

To set up encrypted communication, run
```
sudo openssl dhparam -out /etc/nginx/dhparam.pem 4096
```
and modify `/etc/nginx/nginx.conf` to have only the following lines:
```
user www-data;
worker_processes auto;
pid /run/nginx.pid;
include /etc/nginx/modules-enabled/*.conf;

events {
        worker_connections 768;
}

http {
        sendfile on;
        tcp_nopush on;
        types_hash_max_size 2048;

        include /etc/nginx/mime.types;
        default_type application/octet-stream;

        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES128-SHA;
        ssl_prefer_server_ciphers on;
        ssl_dhparam /etc/nginx/dhparam.pem;

        access_log /var/log/nginx/access.log;
        error_log /var/log/nginx/error.log;

        gzip off;

        include /etc/nginx/conf.d/*.conf;
        include /etc/nginx/sites-enabled/*;
}
```
You may use a self-signed certificate (for testing only) or [Let's Encrypt](https://letsencrypt.org/) or a certificate issued by your institution.
To create a self-signed certificate run
```
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/ssl/private/your_server.key -out /etc/ssl/certs/your_server.crt
```

Now create `/etc/nginx/sites-available/some_name` with content
```
map $http_upgrade $connection_upgrade {
        default upgrade;
        '' close;
}

server {
        listen 80 default_server;

        server_name your-server.org;
        return 301 https://$server_name$request_uri;
}

server {
        listen 443 ssl default_server;

        server_name your-server.org;

        ssl_certificate /etc/ssl/certs/your_server.crt;
        ssl_certificate_key /etc/ssl/private/your_server.key;

        root /var/www/html;
        index index.html index.htm index.nginx-debian.html;

        location / {
                try_files $uri $uri/ =404;
        }

}
```
make this configuration active (and default configuration inactive) via
```
cd /etc/nginx/sites-enabled
sudo ln -s ../sites-available/some_name some_name
sudo rm default

sudo nginx -t
sudo systemctl restart nginx
```
The `nginx -t` makes `nginx` check its configuration.
Run the last line only if the check result is okay.

### Podman

Install Podman:
```
sudo apt install podman containers-storage
````

## Accounts for container admins

In this section, we add a new JupyterHub (its Podman container) to the host machine.
Each container will run in a separate user account to which the container admin has SSH access.

```{hint}
Standard Linux disk quotas work on a per user basis and cannot be setup for not yet exiting users.
But Ananke's Podman containers use systemd's dynamic user feature resulting in more or less random and temporary user IDs.
Thus, standard Linux quotas won't work.
To prevent a container from filling the host machine's disk, we use separate virtual file systems for each container admin.

The container admin's file system's image file will be a sparse file.
Thus, it requires much less disk space than it's size suggests.
See [Disk quota checks and extension](#disk-quota-checks-and-extension) for commands to check container admins' true disk usage.
```

```{warning}
The quota setup sketched in above hint does not prevent hub users from filling a hub's disk capacity.
But it prevents users from DOSing the whole host machine.
```

### User account

Prepare the container admin's home directory with
```
CONT_ADMIN=testhub_user

sudo truncate -s 20G /home/$CONT_ADMIN.img
sudo mkfs.ext4 /home/$CONT_ADMIN.img
sudo mkdir /home/$CONT_ADMIN
```
Then add the line
```
/home/testhub_user.img /home/testhub_user ext4 loop,rw,nosuid,nodev    0    3
```
to `/etc/fstab` and run
```
sudo systemctl daemon-reload
sudo mount /home/$CONT_ADMIN
sudo adduser $CONT_ADMIN
sudo cp -r /etc/skel/.
/home/$CONT_ADMIN/
sudo chown -R $CONT_ADMIN:$CONT_ADMIN /home/$CONT_ADMIN
sudo chmod -R go-rwx /home/$CONT_ADMIN
```
(`adduser` will complain about already existing home directory.
This can be safely ignored.)

Do not forget to tell the container admin to change his or her password at first login!

### SSH access

To activate SSH access, modify corresponding line in `/etc/ssh/sshd_config`:
```
AllowUsers your_username testhub_user
```
Then restart `sshd`:
```
sudo systemctl restart sshd
```
Run
```
sudo mkdir /home/testhub_user/.ssh
```
Get the new container admin's public key and write it to the file `/home/testhub_user/.ssh/authorized_keys`.
Then
```
sudo chown -R testhub_user:testhub_user /home/testhub_user/.ssh
sudo chmod -R go-rwx /home/testhub_user/.ssh
```

Run the command
```
sudo loginctl enable-linger testhub_user
```
This tells `systemd` not to stop the user's Podman containers on logout.

### Port and hub name

Open `/etc/nginx/sites-available/your-server` and place
```
        location /testhub/ {
                proxy_pass http://127.0.0.1:8000;

                proxy_redirect   off;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header Host $host;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;

                proxy_set_header Upgrade $http_upgrade;
                proxy_set_header Connection $connection_upgrade;
        }
```
in the `server` block right above the `location /` line.
Then
```
sudo nginx -t
sudo systemctl restart nginx.service
```
Provide the location (`testhub`) and the port (`8000` in `proxy_pass` line) to container admin.

For each container on the machine use different location and different port.

## Regular maintenance work

At least weekly we should check the system for problems und install updates.
Note that following the above installation instructions, there will be no automatic updates!

### Updates

Run
```
sudo apt update
sudo apt list --upgradable
```
und check the list of available updates (else you do not know what package might have killed your system).
Then run
```
sudo apt upgrade
```

You should also have a look at vulnerable packages.
Problems repairable by updating packages:
```
debsecan --suite bookworm --format report --only-fixed
```
All vulnerable packages (including ones not repairable by update at the moment):
```
debsecan --suite bookworm --format report
```

````{important}
If you have to reboot the machine after an update (new kernel version, for instance), all Podman container's on the machine will be stopped.
Thus, container admins have to restart their containers with
```
podman restart container_name_or_id
```
````

### Malware

Run
```
sudo chkrootkit
sudo rkhunter --check
```
and check the output.
For each alert, carefully check whether you are in trouble or if it's a false positive.

Run Tripwire to see modifications to system files:
```
cd ~
sudo tripwire --check -r report.twr
```
If there are modifications and modifications are okay (!) run
```
sudo tripwire --update -a -r report.twr
```
to tell Tripwire that modifications are okay.

### Login attempts

Have a look at the list of failed logins:
```
sudo last -f /var/log/btmp
```
Is someone trying to get access with brute-force or other methods? Did someone try to log in as you?

You may also have a look at all past logins to see you are working on your machine:
```
sudo last
```

Most recent login for each user:
```
sudo lastlog
```

### Services and connections

Have a look at all active background services:
```
sudo systemctl list-unit-files --state=enabled
```
Something unusual here?

Unusual network connections?
```
sudo lsof -i
```

### General security scan

Every time you modified the system (updates, config changes), run
```
sudo lynis audit system
```
to get hints for improving security.

### System load

System load reports can be shown with [`sar`](https://manpages.debian.org/bookworm/sysstat/sar.sysstat.1.en.html) and [`iostat`](https://manpages.debian.org/bookworm/sysstat/iostat.1.en.html).
Try
```
sar -q ALL -f /var/log/sysstat/saDD
```
where `DD` is the day of the month.
This shows different statistics from which we see whether the machine had been at its maximum load that day.
Many other statistics are available, too.
For `iostat` try
```
iostat -N --human --pretty
```
This prints CPU and disk usage statistics.

(disk-quota-checks-and-extension)=
### Disk quota checks and extension

List disk usage with
```
du -h /home/*.img
```

Extend a container admin's maximum home directory size by
```
CONT_ADMIN=testhub_user

sudo truncate -s +5G /home/$CONT_ADMIN.img
sudo umount /home/$CONT_ADMIN.img
sudo e2fsck -f /home/$CONT_ADMIN.img
sudo resize2fs /home/$CONT_ADMIN.img
sudo mount /home/$CONT_ADMIN.img
```
If `umount` fails with `device is busy` run
```
sudo lsof /home/$CONT_ADMIN
```
and kill corresponding processes.
Alternatively (or additionally), run
```
sudo fuser -mv /home/$CONT_ADMIN.img
```
to see processes using the file system and run
```
sudo fuser -mkv /home/$CONT_ADMIN.img
```
to kill them.

## Optional features

Features described below may be relevant to some users only.

(host-admins-gpu)=
### GPU support

If the host machine's GPUs shall be accessible inside Podman containers, the steps below should be a good starting point.
Here we only cover NVIDIA GPUs.
Instructions are compiled and adapted from different sources:
* [NVIDIA CUDA Installation Guide for Linux, Pre-installation Actions](https://docs.nvidia.com/cuda/cuda-installation-guide-linux/index.html#pre-installation-actions)
* [NVIDIA CUDA Installation Guide for Linux, Device Node Verification](https://docs.nvidia.com/cuda/cuda-installation-guide-linux/index.html#device-node-verification)
* [NVIDIA Container Toolkit Installation Guide, Container Device Interface (CDI) Support](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html#container-device-interface-cdi-support)
* [NVIDIA Container Toolkit Installation Guide, podman](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html#id7)
* [CDI - The Container Device Interface, Podman configuration](https://github.com/container-orchestrated-devices/container-device-interface#podman-configuration)
* [ArchWiki, Podman, NVIDIA GPUs](https://wiki.archlinux.org/title/Podman#NVIDIA_GPUs)
* [NVIDIA GPU 'passthrough' to lxc containers on Proxmox 6 for NVENC in Plex](https://matthieu.yiptong.ca/tag/plex/)

Things change rapidly, so consult those sources, too.

#### Install GPU drivers

Debian's NVIDIA driver packages require installation of some (not all) X-Server components.
Maybe it's not necessary, but we should tell the system to not boot into any graphical environment:
```
sudo systemctl set-default multi-user.target
```

GPUs visible to the system?
```
sudo apt install pciutils
lspci | grep -i nvidia
```

GPU drivers are on Debian's non-free repo.
Thus, append `non-free` to the relevant line in `/etc/apt/sources.list`.
Then
```
apt update
apt search nvidia
```
Depending on your GPU you have to install `nvidia-driver` or `nvidia-tesla-driver` or maybe something different:
```
sudo apt install nvidia-tesla-driver nvidia-cudnn
```
(note that installing `nvidia-cudnn` may be unnecessary).

Now
```
nvidia-smi
```
should show all your GPUs and current driver version.

#### Podman with GPUs

We need an NVIDIA repo for installing `nvidia-container-toolkit`.
To make the repo available to `apt` run
```
sudo apt install curl

cd ~
curl -o nvidia.asc https://nvidia.github.io/libnvidia-container/gpgkey
cat nvidia.asc | gpg --dearmor > nvidia.gpg
sudo install -o root -g root -m 644 nvidia.gpg /usr/share/keyrings/nvidia-archive-keyring.gpg
rm nvidia.asc
rm nvidia.gpg
```
Then create the file `/etc/apt/sources.list.d/nvidia-container-toolkit.list` with content
```
deb [signed-by=/usr/share/keyrings/nvidia-archive-keyring.gpg] https://nvidia.github.io/libnvidia-container/stable/debian10/amd64 /
```
(note that although we are running Debian 12 we have to provide `debian10` here until NVIDIA officially supports Debian 12).

Install `nvidia-container-toolkit` with
```
sudo apt update
sudo apt install nvidia-container-toolkit-base
```
and check with
```
nvidia-ctk --version
```

Now create the file `/usr/local/bin/nvidia-start.sh` with content
```
#!/bin/bash

/sbin/modprobe nvidia

if [ "$?" -eq 0 ]; then
  # Count the number of NVIDIA controllers found.
  NVDEVS=`lspci | grep -i NVIDIA`
  N3D=`echo "$NVDEVS" | grep "3D controller" | wc -l`
  NVGA=`echo "$NVDEVS" | grep "VGA compatible controller" | wc -l`

  N=`expr $N3D + $NVGA - 1`
  for i in `seq 0 $N`; do
    mknod -m 666 /dev/nvidia$i c 195 $i
  done

  mknod -m 666 /dev/nvidiactl c 195 255

else
  exit 1
fi

/sbin/modprobe nvidia-uvm

if [ "$?" -eq 0 ]; then
  # Find out the major device number used by the nvidia-uvm driver
  D=`grep nvidia-uvm /proc/devices | awk '{print $1}'`

  mknod -m 666 /dev/nvidia-uvm c $D 0
  mknod -m 666 /dev/nvidia-uvm-tools c $D 0
else
  exit 1
fi
```
and set permissions with
```
sudo chmod o+x /usr/local/bin/nvidia-start.sh
```
Then create `/etc/systemd/system/nvidia-start.service` with content
```
[Unit]
Description=Runs /usr/local/bin/nvidia-start.sh

[Service]
ExecStart=/usr/local/bin/nvidia-start.sh

[Install]
WantedBy=multi-user.target
```
and activate the `systemd` service with
```
sudo systemctl daemon-reload
sudo systemctl enable nvidia-start.service
sudo systemctl start nvidia-start.service
```

Container toolkit should work now, and we can generate information relevant to Podman:
```
sudo nvidia-ctk cdi generate --output=/etc/cdi/nvidia.yaml
sudo chmod o+rx /etc/cdi
```
Running
```
cat /etc/cdi/nvidia.yaml | grep "name:"
```
should show all GPU identifiers (maybe including `all`).
```{important}
The above `nvidia-ctk cdi generate` step has to be rerun after each update of NVIDIA GPU drivers! Else Podman won't work with GPU.
```

To make GPUs available in rootless Podman containers in `/etc/nvidia-container-runtime/config.toml` add/modify the line
```
no-cgroups = true
```

Test the setup by running `nvidia-smi` in a container:
```
podman run --rm --device nvidia.com/gpu=all ubuntu nvidia-smi -L
```

Whenever GPUs shall be available in a Podman container, append
```
--device nvidia.com/gpu=all
```
to `podman run`, where `all` may be replaced by one of the GPU identifiers shown by the `cat` command above.

