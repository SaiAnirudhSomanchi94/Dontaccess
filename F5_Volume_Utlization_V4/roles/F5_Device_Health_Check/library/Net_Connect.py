from __future__ import absolute_import
import re, time
import sys
import imp
import pickle
import logging
########################################################################################################################
# Connectivity
########################################################################################################################

def Connectivity(JumpServer, J_USERNAME, J_PASSWORD, ip, D_Username, D_Password, path, commands):
    try:
        PROJECT_PATH = path
        fp = open("/tmp/shared.pkl", "wb")
        i = 1
        pickle.dump(PROJECT_PATH, fp)
        print(PROJECT_PATH)
        sys.path.insert(1, str(PROJECT_PATH) + r'/roles/F5_Device_Health_Check/packages/')
        from Device_Modules import ConnectHandler, redispatch
        JumpServer = re.findall('([\d.]+)', str(JumpServer))
        if len(JumpServer) != 0:
            try:
                jumpserver = {"device_type": "terminal_server", "ip": str(JumpServer[0]), "username": J_USERNAME,
                              "password": J_PASSWORD, "global_delay_factor": 3}
                net_connect = ConnectHandler(**jumpserver)
                print(net_connect)
                time.sleep(1)
                print(net_connect.find_prompt())
                print('Execution in progess')
                net_connect.write_channel("ssh -p22 -o KexAlgorithms=+diffie-hellman-group1-sha1 -o HostKeyAlgorithms=+ssh-dss  " + str(D_Username) + "@" + ip + '\n')
                max_loops = 60
                val = ''
                i = 1
                num = ''
                while i <= max_loops:
                    output = net_connect.read_channel()
                    num += output
                    print(output)
                    if 'yes/no' in output:
                        net_connect.write_channel('yes\n')
                        time.sleep(.5)
                        net_connect.write_channel(str(D_Password) + '\n')
                        output = net_connect.read_channel()
                        if '>' in output or '#' in output:
                            break
                    if 'ssword' in output:
                        a = 'password entered'
                        net_connect.write_channel(str(D_Password) + '\n')
                        # print(net_connect.device_password)
                        print('Entered Pasword')
                        time.sleep(.2)
                        output = net_connect.read_channel()
                        print(output)
                        if '#' in output:
                            val = 'break'
                            break
                    if 'timed out' in output:
                        print('SSH Connection timed out ')
                        time.sleep(.5)
                        val = 'break'
                    time.sleep(.5)
                    if '>' in output or '#' in output :
                        val = 'break'
                        break
                    i += 1
                    # print(i)
                    if i == 61 or val == 'break':
                        break
                    # net_connect.disconnect()
                    # net_connect.disconnect()
                redispatch(net_connect, device_type='f5_ltm')
            except Exception as e:
                    response_content = str('Issue in Device Connectivity, Manual action is required-' + str(i))
                    decision = 0
        else:
            jumpserver = {"device_type": 'f5_ltm', "ip": str(ip), "username": D_Username,
                          "password": D_Password, "global_delay_factor": 3}
            net_connect = ConnectHandler(**jumpserver)
        print(net_connect)
        try:
            response_content = ''
            for command in commands:
                response_content += '\n' + '~' * 100 + '\n'
                response_content += str(command)
                response_content += '\n' + '~' * 100 + '\n'
                if 'show' in command or 'run' in command or 'bash' in command:
                    response_content += net_connect.send_command(command)#, delay_factor=5, max_loops=10000)
                else:
                    response_content += command
                response_content += '\n' + '~' * 100 + '\n'
            # print(response_content)
            decision = 1
        except Exception as e:
            response_content = str('Issue in Device Connectivity')+ str(e)+'actual issue:'+str(comm_line)
            decision = 0
    except Exception as e:
        response_content = str('Issue in Device Connectivity') + str(e)
        decision = 0
    return response_content, int(decision)


def main():
    module = AnsibleModule(
        argument_spec=dict(
        IP=dict(required=True),
        d_username=dict(required=True),
		d_password=dict(required=True),
		JumpServer=dict(required=True),
        j_username= dict(required= True),
        j_password= dict(required=True),
        path=dict(required=True),
        commands=dict(required=True, type=list)
        ),
    )
    IP = module.params['IP']
    Username = module.params['d_username']
    Password = module.params['d_password']
    JumpServer = module.params['JumpServer']
    J_Username = module.params['j_username']
    J_Password = module.params['j_password']
    path = module.params['path']
    commands = module.params['commands']
    Result_main, decision = Connectivity(JumpServer,J_Username, J_Password,IP, Username, Password, path, commands)
    if decision == 1:
        module.exit_json(changed=False, meta=Result_main, decision=int(decision))
    else:
        module.exit_json(changed=True, meta=Result_main, decision=int(decision))



from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()