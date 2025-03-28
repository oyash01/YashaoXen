#!/usr/bin/env python3

import os
import logging
import subprocess
from typing import List, Dict, Any
from pathlib import Path
import json

class SecurityManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def setup_container_isolation(self, container_name: str, config: Dict[str, Any]) -> None:
        """Set up container isolation with security measures"""
        try:
            # Create dedicated network namespace
            namespace = f"netns_{container_name}"
            self._create_network_namespace(namespace)
            
            # Set up network isolation
            self._configure_network_isolation(namespace, config)
            
            # Configure seccomp profile
            self._setup_seccomp_profile(container_name)
            
            # Set up AppArmor profile
            self._setup_apparmor_profile(container_name)
            
            # Configure resource limits
            self._setup_resource_limits(container_name, config)
            
            self.logger.info(f"Container isolation configured for {container_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to set up container isolation: {e}")
            raise
            
    def setup_network_security(self, container_name: str, config: Dict[str, Any]) -> None:
        """Configure network security rules"""
        try:
            # Set up base iptables rules
            self._setup_base_iptables()
            
            # Configure container-specific rules
            self._setup_container_iptables(container_name, config)
            
            # Set up network namespace routing
            self._setup_namespace_routing(container_name)
            
            # Configure DNS security
            self._setup_dns_security(container_name)
            
            self.logger.info(f"Network security configured for {container_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to set up network security: {e}")
            raise
            
    def _create_network_namespace(self, namespace: str) -> None:
        """Create isolated network namespace"""
        subprocess.run(['ip', 'netns', 'add', namespace], check=True)
        
        # Create veth pair
        veth0 = f"veth0_{namespace}"
        veth1 = f"veth1_{namespace}"
        subprocess.run(['ip', 'link', 'add', veth0, 'type', 'veth', 'peer', 'name', veth1], check=True)
        
        # Move one end to namespace
        subprocess.run(['ip', 'link', 'set', veth1, 'netns', namespace], check=True)
        
        # Configure interfaces
        subprocess.run(['ip', 'addr', 'add', '10.0.0.1/24', 'dev', veth0], check=True)
        subprocess.run(['ip', 'netns', 'exec', namespace, 'ip', 'addr', 'add', '10.0.0.2/24', 'dev', veth1], check=True)
        
        # Bring up interfaces
        subprocess.run(['ip', 'link', 'set', veth0, 'up'], check=True)
        subprocess.run(['ip', 'netns', 'exec', namespace, 'ip', 'link', 'set', 'veth1', 'up'], check=True)
            
    def _configure_network_isolation(self, namespace: str, config: Dict[str, Any]) -> None:
        """Configure network isolation for namespace"""
        # Set up routing
        subprocess.run(['ip', 'netns', 'exec', namespace, 'ip', 'route', 'add', 'default', 'via', '10.0.0.1'], check=True)
        
        # Enable IP forwarding
        with open('/proc/sys/net/ipv4/ip_forward', 'w') as f:
            f.write('1')
            
        # Configure NAT
        subprocess.run([
            'iptables', '-t', 'nat', '-A', 'POSTROUTING',
            '-s', '10.0.0.0/24', '-j', 'MASQUERADE'
        ], check=True)
            
    def _setup_seccomp_profile(self, container_name: str) -> None:
        """Set up seccomp profile for container"""
        profile = {
            "defaultAction": "SCMP_ACT_ERRNO",
            "architectures": ["SCMP_ARCH_X86_64"],
            "syscalls": [
                {
                    "names": [
                        "accept", "bind", "connect", "socket",
                        "read", "write", "close", "fstat",
                        "lseek", "mmap", "mprotect", "munmap",
                        "brk", "rt_sigaction", "rt_sigprocmask",
                        "rt_sigreturn", "ioctl", "access", "pipe",
                        "select", "mremap", "sched_yield", "msync",
                        "mincore", "madvise", "shmget", "shmat",
                        "shmctl", "dup", "dup2", "pause", "nanosleep",
                        "getitimer", "alarm", "setitimer", "getpid",
                        "sendfile", "socket", "connect", "accept",
                        "sendto", "recvfrom", "sendmsg", "recvmsg",
                        "shutdown", "bind", "listen", "getsockname",
                        "getpeername", "socketpair", "setsockopt",
                        "getsockopt", "clone", "fork", "vfork",
                        "execve", "exit", "wait4", "kill", "uname",
                        "semget", "semop", "semctl", "shmdt",
                        "msgget", "msgsnd", "msgrcv", "msgctl",
                        "fcntl", "flock", "fsync", "fdatasync",
                        "truncate", "ftruncate", "getcwd", "chdir",
                        "fchdir", "rename", "mkdir", "rmdir",
                        "creat", "link", "unlink", "symlink",
                        "readlink", "chmod", "fchmod", "chown",
                        "fchown", "lchown", "umask", "gettimeofday",
                        "getrlimit", "getrusage", "sysinfo",
                        "times", "ptrace", "getuid", "syslog",
                        "getgid", "setuid", "setgid", "geteuid",
                        "getegid", "setpgid", "getppid", "getpgrp",
                        "setsid", "setreuid", "setregid",
                        "getgroups", "setgroups", "setresuid",
                        "getresuid", "setresgid", "getresgid",
                        "getpgid", "setfsuid", "setfsgid", "getsid",
                        "capget", "capset", "rt_sigpending",
                        "rt_sigtimedwait", "rt_sigqueueinfo",
                        "rt_sigsuspend", "sigaltstack",
                        "utime", "mknod", "uselib", "personality",
                        "ustat", "statfs", "fstatfs", "sysfs",
                        "getpriority", "setpriority", "sched_setparam",
                        "sched_getparam", "sched_setscheduler",
                        "sched_getscheduler", "sched_get_priority_max",
                        "sched_get_priority_min", "sched_rr_get_interval",
                        "mlock", "munlock", "mlockall", "munlockall",
                        "vhangup", "modify_ldt", "pivot_root",
                        "_sysctl", "prctl", "arch_prctl", "adjtimex",
                        "setrlimit", "chroot", "sync", "acct",
                        "mount", "umount2", "swapon", "swapoff",
                        "reboot", "sethostname", "setdomainname",
                        "iopl", "ioperm", "create_module",
                        "init_module", "delete_module", "get_kernel_syms",
                        "query_module", "quotactl", "nfsservctl",
                        "getpmsg", "putpmsg", "afs_syscall",
                        "tuxcall", "security", "gettid",
                        "readahead", "setxattr", "lsetxattr",
                        "fsetxattr", "getxattr", "lgetxattr",
                        "fgetxattr", "listxattr", "llistxattr",
                        "flistxattr", "removexattr", "lremovexattr",
                        "fremovexattr", "tkill", "time",
                        "futex", "sched_setaffinity",
                        "sched_getaffinity", "set_thread_area",
                        "io_setup", "io_destroy", "io_getevents",
                        "io_submit", "io_cancel", "get_thread_area",
                        "lookup_dcookie", "epoll_create",
                        "epoll_ctl_old", "epoll_wait_old",
                        "remap_file_pages", "getdents64",
                        "set_tid_address", "restart_syscall",
                        "semtimedop", "fadvise64", "timer_create",
                        "timer_settime", "timer_gettime",
                        "timer_getoverrun", "timer_delete",
                        "clock_settime", "clock_gettime",
                        "clock_getres", "clock_nanosleep",
                        "exit_group", "epoll_wait", "epoll_ctl",
                        "tgkill", "utimes", "vserver",
                        "mbind", "set_mempolicy", "get_mempolicy",
                        "mq_open", "mq_unlink", "mq_timedsend",
                        "mq_timedreceive", "mq_notify",
                        "mq_getsetattr", "kexec_load",
                        "waitid", "add_key", "request_key",
                        "keyctl", "ioprio_set", "ioprio_get",
                        "inotify_init", "inotify_add_watch",
                        "inotify_rm_watch", "migrate_pages",
                        "openat", "mkdirat", "mknodat",
                        "fchownat", "futimesat", "newfstatat",
                        "unlinkat", "renameat", "linkat",
                        "symlinkat", "readlinkat", "fchmodat",
                        "faccessat", "pselect6", "ppoll",
                        "unshare", "set_robust_list",
                        "get_robust_list", "splice", "tee",
                        "sync_file_range", "vmsplice",
                        "move_pages", "utimensat", "epoll_pwait",
                        "signalfd", "timerfd_create",
                        "eventfd", "fallocate", "timerfd_settime",
                        "timerfd_gettime", "accept4",
                        "signalfd4", "eventfd2", "epoll_create1",
                        "dup3", "pipe2", "inotify_init1",
                        "preadv", "pwritev", "rt_tgsigqueueinfo",
                        "perf_event_open", "recvmmsg",
                        "fanotify_init", "fanotify_mark",
                        "prlimit64", "name_to_handle_at",
                        "open_by_handle_at", "clock_adjtime",
                        "syncfs", "sendmmsg", "setns",
                        "getcpu", "process_vm_readv",
                        "process_vm_writev", "kcmp",
                        "finit_module", "sched_setattr",
                        "sched_getattr", "renameat2",
                        "seccomp", "getrandom", "memfd_create",
                        "kexec_file_load", "bpf", "execveat",
                        "userfaultfd", "membarrier", "mlock2",
                        "copy_file_range", "preadv2", "pwritev2",
                        "pkey_mprotect", "pkey_alloc",
                        "pkey_free", "statx",
                        "io_pgetevents", "rseq"
                    ],
                    "action": "SCMP_ACT_ALLOW"
                }
            ]
        }
        
        profile_path = Path(f"/etc/docker/seccomp/{container_name}.json")
        profile_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(profile_path, 'w') as f:
            json.dump(profile, f, indent=2)
            
    def _setup_apparmor_profile(self, container_name: str) -> None:
        """Set up AppArmor profile for container"""
        profile = f"""
#include <tunables/global>

profile {container_name} flags=(attach_disconnected,mediate_deleted) {{
    #include <abstractions/base>
    #include <abstractions/nameservice>
    
    network,
    capability net_admin,
    capability net_raw,
    
    deny @{PROC}/* w,   # deny write for all files directly in /proc
    deny @{PROC}/{[^1-9]*,sys/kernel/shm*} rw,
    deny @{PROC}/sysrq-trigger rwklx,
    deny @{PROC}/mem rwklx,
    deny @{PROC}/kmem rwklx,
    deny @{PROC}/kcore rwklx,
    deny mount,
    deny /sys/[^f]*/** wklx,
    deny /sys/f[^s]*/** wklx,
    deny /sys/fs/[^c]*/** wklx,
    deny /sys/fs/c[^g]*/** wklx,
    deny /sys/fs/cg[^r]*/** wklx,
    deny /sys/firmware/efi/efivars/** rwklx,
    deny /sys/kernel/security/** rwklx,
    
    # Allow limited reads from /proc for own pid
    owner @{PROC}/@{pid}/stat r,
    owner @{PROC}/@{pid}/cmdline r,
    owner @{PROC}/@{pid}/fd/ r,
    
    /etc/earnapp/** r,
    owner /tmp/** rw,
    owner /var/tmp/** rw,
}}
"""
        
        profile_path = Path(f"/etc/apparmor.d/containers/{container_name}")
        profile_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(profile_path, 'w') as f:
            f.write(profile)
            
        # Load AppArmor profile
        subprocess.run(['apparmor_parser', '-r', '-W', str(profile_path)], check=True)
            
    def _setup_resource_limits(self, container_name: str, config: Dict[str, Any]) -> None:
        """Set up resource limits for container"""
        resources = config.get('container', {}).get('resources', {})
        
        # Create cgroup
        cgroup_path = Path(f"/sys/fs/cgroup/memory/{container_name}")
        cgroup_path.mkdir(parents=True, exist_ok=True)
        
        # Set memory limit
        memory_limit = resources.get('memory_limit', '1G')
        with open(cgroup_path / 'memory.limit_in_bytes', 'w') as f:
            f.write(str(self._parse_memory_limit(memory_limit)))
            
        # Set CPU limit
        cpu_shares = resources.get('cpu_shares', 1024)
        with open(cgroup_path / 'cpu.shares', 'w') as f:
            f.write(str(cpu_shares))
            
    def _setup_base_iptables(self) -> None:
        """Set up base iptables rules"""
        # Flush existing rules
        subprocess.run(['iptables', '-F'], check=True)
        subprocess.run(['iptables', '-X'], check=True)
        
        # Set default policies
        subprocess.run(['iptables', '-P', 'INPUT', 'DROP'], check=True)
        subprocess.run(['iptables', '-P', 'FORWARD', 'DROP'], check=True)
        subprocess.run(['iptables', '-P', 'OUTPUT', 'DROP'], check=True)
        
        # Allow established connections
        subprocess.run([
            'iptables', '-A', 'INPUT',
            '-m', 'conntrack',
            '--ctstate', 'ESTABLISHED,RELATED',
            '-j', 'ACCEPT'
        ], check=True)
        
        subprocess.run([
            'iptables', '-A', 'OUTPUT',
            '-m', 'conntrack',
            '--ctstate', 'ESTABLISHED,RELATED',
            '-j', 'ACCEPT'
        ], check=True)
            
    def _setup_container_iptables(self, container_name: str, config: Dict[str, Any]) -> None:
        """Set up container-specific iptables rules"""
        # Allow DNS
        subprocess.run([
            'iptables', '-A', 'OUTPUT',
            '-p', 'udp', '--dport', '53',
            '-j', 'ACCEPT'
        ], check=True)
        
        # Allow HTTP/HTTPS
        for port in [80, 443]:
            subprocess.run([
                'iptables', '-A', 'OUTPUT',
                '-p', 'tcp', '--dport', str(port),
                '-j', 'ACCEPT'
            ], check=True)
            
        # Set up NAT for container
        subprocess.run([
            'iptables', '-t', 'nat', '-A', 'POSTROUTING',
            '-s', '10.0.0.0/24',
            '-j', 'MASQUERADE'
        ], check=True)
            
    def _setup_namespace_routing(self, container_name: str) -> None:
        """Set up routing for network namespace"""
        namespace = f"netns_{container_name}"
        
        # Enable IP forwarding in namespace
        subprocess.run([
            'ip', 'netns', 'exec', namespace,
            'sysctl', '-w', 'net.ipv4.ip_forward=1'
        ], check=True)
        
        # Set up default route
        subprocess.run([
            'ip', 'netns', 'exec', namespace,
            'ip', 'route', 'add', 'default',
            'via', '10.0.0.1'
        ], check=True)
            
    def _setup_dns_security(self, container_name: str) -> None:
        """Set up DNS security for container"""
        namespace = f"netns_{container_name}"
        
        # Create resolv.conf for namespace
        resolv_conf = f"""
nameserver 1.1.1.1
nameserver 8.8.8.8
options edns0
options trust-ad
"""
        
        resolv_path = Path(f"/etc/netns/{namespace}")
        resolv_path.mkdir(parents=True, exist_ok=True)
        
        with open(resolv_path / 'resolv.conf', 'w') as f:
            f.write(resolv_conf)
            
    def _parse_memory_limit(self, limit: str) -> int:
        """Convert memory limit string to bytes"""
        units = {'B': 1, 'K': 1024, 'M': 1024*1024, 'G': 1024*1024*1024}
        unit = limit[-1].upper()
        if unit not in units:
            raise ValueError(f"Invalid memory limit unit: {unit}")
        return int(limit[:-1]) * units[unit] 