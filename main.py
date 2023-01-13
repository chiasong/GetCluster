import threading
import tkinter as tk
from tkinter import ttk, INSERT
from tkinter import scrolledtext as st
import openpyxl
import paramiko
import time


class App(ttk.Frame):
    def __init__(self):
        ttk.Frame.__init__(self)

        # Create widgets
        self.button = None
        self.entry_password = None
        self.input_list = None
        self.entry_username = None
        self.log = None
        self.label = None
        self.widgets_frame = None
        self.setup_widgets()

    def setup_widgets(self):
        # Create a Frame for input widgets
        self.widgets_frame = ttk.Frame(self, padding=(0, 0, 0, 0))
        self.widgets_frame.grid(
            row=0, column=0, padx=10, pady=5, sticky="nsew")

        # Label
        self.label = ttk.Label(self.widgets_frame, text="请输入集群IP", justify="center",
                               font=("-size", 12))
        self.label.grid(row=0, column=0)

        # Input List
        self.input_list = st.ScrolledText(self.widgets_frame, width=20, height=30)
        self.input_list.grid(row=1, column=0, pady=5, sticky='nsew')

        # Log
        self.label = ttk.Label(self.widgets_frame, text="Log",
                               font=("-size", 12))
        self.label.grid(row=0, column=1)
        # self.log = st.ScrolledText(self.widgets_frame, height=10)
        self.log = st.ScrolledText(self.widgets_frame, width=30, height=30)
        self.log.grid(row=1, column=1, pady=5, sticky='nsew')
        self.log.config(state='disabled')

        # Entry
        self.label = ttk.Label(self.widgets_frame, text="用户名:",
                               font=("-size", 12))
        self.label.grid(row=2, column=0, sticky='w')

        self.entry_username = ttk.Entry(self.widgets_frame, width=20)
        self.entry_username.grid(row=2, column=0, padx=45, sticky="w")

        self.label = ttk.Label(self.widgets_frame, text="密码:",
                               font=("-size", 12))
        self.label.grid(row=3, column=0, sticky="w")

        self.entry_password = ttk.Entry(self.widgets_frame, width=20)
        self.entry_password.grid(row=3, column=0, padx=45, sticky="w")

        # Upload Button
        self.button = ttk.Button(self.widgets_frame, text="开始检测",
                                 command=lambda: self.thread_it(self.input_list.get(1.0, 'end'),
                                                                self.entry_username.get(), self.entry_password.get()))
        self.button.grid(row=3, column=1, padx=0, pady=10, sticky="e")

        self.entry_username.insert(0, 'root')
        self.entry_password.insert(0, 'suhang123')
        self.input_list.insert(INSERT, '43.139.14.82')

    def check(self, images_list, username, password):
        start = time.process_time_ns()
        # 中间写上代码块
        info_xl = openpyxl.Workbook()
        sheet = info_xl.active
        sheet.append(['IP地址', '系统版本', '防火墙', '主机名', 'CPU型号', '核心数', '内存占用', '内存大小', '硬盘占用',
                      '硬盘大小'])

        self.show_log('任务开始')
        images_list = [i for i in images_list.split('\n') if i != '']
        self.show_log('IP列表中有' + str(len(images_list)) + '台')
        for ip in images_list:
            self.show_log('开始获取' + str(ip) + '的信息')

            client_from = paramiko.SSHClient()
            client_from.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client_from.connect(hostname=ip, port=22, username=username,
                                password=password)
            # System_Info
            stdin, stdout, stderr = client_from.exec_command('cat /etc/redhat-release')
            systeminfo = (stdout.read().decode().split('\n')[0])[0:-1]
            # self.show_log(systeminfo)

            # Firewall_Status
            stdin, stdout, stderr = client_from.exec_command('systemctl status firewalld')
            fw_status = list(stdout.read().decode().split('\n'))
            fw = ''
            for fw_line in fw_status:
                if fw_line.startswith('   Active:'):
                    fw = fw_line.strip()
                    break
                elif fw_line.startswith('Unit'):
                    fw = fw_line.strip()
                    break
            # self.show_log(fw)

            # Hostname
            stdin, stdout, stderr = client_from.exec_command('hostname')
            hostname = stdout.read().decode().split('\n')[0]
            # self.show_log(hostname)

            # CPU_Info
            stdin, stdout, stderr = client_from.exec_command('cat /proc/cpuinfo | grep "model name" --color=never')
            cpu_info = list(stdout.read().decode().split('\n'))
            cpu_count = 0
            for ci_line in cpu_info:
                if ci_line.startswith('model name'):
                    cpu_count += 1
            cpu_info = (cpu_info[0].split(':')[1])[1:-1]
            cpu_count = str(cpu_count) + 'Core'
            # self.show_log(cpu_info)
            # self.show_log(cpu_count)

            # Mem_Info
            stdin, stdout, stderr = client_from.exec_command('cat /proc/meminfo | head -n 5')
            meminfo = list(stdout.read().decode().split('\n'))
            mem_total = 0
            mem_free = 0
            mem_buffers = 0
            mem_cache = 0
            for mem_line in meminfo:
                if mem_line.startswith('MemTotal:'):
                    mem_total = int(mem_line.split()[1])
                elif mem_line.startswith('MemFree:'):
                    mem_free = int(mem_line.split()[1])
                elif mem_line.startswith('Buffers:'):
                    mem_buffers = int(mem_line.split()[1])
                elif mem_line.startswith('Cached:'):
                    mem_cache = int(mem_line.split()[1])
                else:
                    continue
            men_usage = '%.2f%%' % float(
                (mem_total - mem_free - mem_buffers - mem_cache) / mem_total * 100)
            mem_total = '%.2fG' % float(mem_total / 1024 / 1024)
            # self.show_log(usage_percent)
            # self.show_log(mem_total)

            # Disk_Info
            stdin, stdout, stderr = client_from.exec_command('df -lmP | grep "^/dev" --color=never')
            diskinfo = [i for i in list(stdout.read().decode().split('\n')) if i != '']
            disk_usage = 0
            disk_total = 0
            for dk_line in diskinfo:
                disk_usage += float(int([i for i in dk_line.split(' ') if i != ''][2]) / 1024)
                disk_total += float(int([i for i in dk_line.split(' ') if i != ''][1]) / 1024)
            disk_usage = '%.2f%s' % (disk_usage, "G")
            disk_total = '%.2f%s' % (disk_total, "G")
            # self.show_log(used_total)
            # self.show_log(disk_total)
            client_from.close()
            sheet.append([ip, systeminfo, fw, hostname, cpu_info, cpu_count, men_usage, mem_total, disk_usage,
                          disk_total])
            self.show_log(str(ip) + '的信息获取完成')
        info_xl.save(time.strftime('%Y%m%d%H%M') + '.xlsx')
        end = time.process_time_ns()
        self.show_log('任务完成')
        self.show_log('任务用时: %s 秒' % ((end - start) / 100000000))
        self.show_log('表格文件保存在当前路径下')
        self.show_log('文件名为:' + time.strftime('%Y%m%d%H%M') + '.xlsx')

    def thread_it(self, images_list, username, password):
        t = threading.Thread(target=self.check, args=(images_list, username, password))
        t.setDaemon(True)
        t.start()

    def show_log(self, logs):
        if logs:
            self.log.config(state='normal')
            self.log.insert('end', logs + '\n')
            self.log.yview_moveto(1)
            self.log.config(state='disabled')
        else:
            pass


if __name__ == "__main__":
    root = tk.Tk()
    root.title("集群信息收集工具")

    # Simply set the theme
    root.tk.call("source", "azure.tcl")
    root.tk.call("set_theme", "dark")

    app = App()
    app.pack(fill="both", expand=True)

    # Set a minsize for the window, and place it in the middle
    root.update()
    root.minsize(root.winfo_width(), root.winfo_height())
    x_cordinate = int((root.winfo_screenwidth() / 2) - (root.winfo_width() / 2))
    y_cordinate = int((root.winfo_screenheight() / 2) - (root.winfo_height() / 2))
    root.geometry("+{}+{}".format(x_cordinate, y_cordinate - 20))

    root.mainloop()
