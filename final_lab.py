import os
import pickle
import math
import threading
import re
import socket
from _thread import *

manual_dict = {'freemem': 'freemem:\n    Purpose: View number of free blocks in memory and open file table.\n    example: E:/>freemem','map': 'map: To view the whole directory structure.', 'man': 'man [optional: command_name]\nPurpose: View the manual of all commands.\nexample: E:>man\nanother example: E:> man cd or E:>man pwd',
               'pwd': 'To print working directory.', 'copy': 'copy [FILENAME]:\n	Purpose: Copy content of one file to the other in the same directory.\n	example: copy file1.txt file2.txt.',
               'ls': 'to list files and folders in current directory.',
               'cd': 'cd [DIRECTORY_NAME]: Change to an EXISTING directory within the current directory.\nexample:\nE:/>cd folder1', 'mkdir': 'mkdir [DIRECTORY_NAME]: Make a new directory within the current directory. Error will occur if directory already exists.\nexample:\nE:/>mkdir folder1',
               'mv': 'mv [FILENAME] [DESTINATION_PATH]: mv an EXISTING file in the CURRENT DIRECTORY to a VALID destination path. Only absolute paths (e.g: E:/folder1/subfolder1/) are supported.\n    example:\n	E:/>mv file.txt E:/folder1/\n\nValid Path Example: E:/folder1/', 'touch': 'touch [FILENAME]:\n	Same as Create <fname> given in lab instruction manual.\n	Purpose: create a new file in the current directory. Complete Pathnames (e.g: touch E:/folder1/file.txt) are not supported.\n	example: \n		E:/>touch file1.txt',
               'write_to_file': 'write_to_file [FILENAME] "[text]"  OR\nwrite_to_file [FILENAME] "[text]" [start_index]:\nPurpose: Writing contents of an existing file. You can also specify the specify the starting index to write the text to the file.\n	Note: write text within quotation marks or an error will occur.\n	example:\n	E:/>write_to_file file1.txt "hello world" OR E:/>write_to_file file1.txt "bye world" 2',
               'read_from_file': 'read_from_file [FILENAME]\n   read_from_file [FILENAME] [start_index] [size]\n	Purpose: Viewing contents of a certain file. You can also specify starting index and no. of characters to read (Starting Index is from 0).\n	example:\n	E:/>read_from_file file1.txt OR read_from_file file1.txt 2',
               'open': 'open [FILENAME]:\n	Purpose: Opens the file, and adds it to the open file table, which means you can write to it, read from it, or trucate it.\n	Example:\n	open file1.txt', 'close': 'close [FILENAME]\n	Purpose: To close an already opened file. This command will remove the file from open file table.\n			 After the file has been closed, it cannot be read, written or trucated. It can be deleted once it is closed.\n	example:\n	close file1.txt',
               'rm': 'rm [FILENAME or DIRECTORYNAME]:\n	Purpose: Removing a file or directory from the current directory. Complete Pathnames (e.g: rm E:/folder1/file.txt) are not supported.\n	example:\n	E:/>rm file1.txt OR rm folder1',
               'trunc': 'trunc [FILENAME],[start_index]:\n	Purpose: Truncate contents of a file in current directory from the start_index.\n	Note: The file must be open to trucate it. Use open command to open the file first.\n	example:\n	E:/>trunc file1.txt 10'}


open_file_table = {}
users = {}

# This function is used to allocate blocks to store the string data
def allocateBlock(data):
    # Calculating the total memory space available ..
    # by multiplying total blocks with block size i.e. 10
    blocksAvailable = blocks["freeBlocks"]
    spaceAvailable = len(blocksAvailable) * 10
    dataLength = len(data)
    block_list = []

    if not blocksAvailable:
        print("No blocks available! Memory is full.")
    elif (dataLength > spaceAvailable):
        print("Not enough free blocks")

    else:
        blocksRequired = math.ceil(dataLength / 10)

        # This loop maintains the block size of 10
        # By writing 10 characters of string per block
        for i in range(blocksRequired):
            currentBlock = blocksAvailable.pop(0)
            block_list.append(currentBlock)
            blocks[currentBlock] = data[0:10]
            data = data[10:]
    return block_list


# This function is used to delete already allocated blocks
# It uses the index of the blocks
def deleteBlock(index):
    blocks["freeBlocks"].insert(0, index)
    del blocks[index]

def show_open_files():
    response = ''
    if len(open_file_table) == 0:
        response = 'No files are open currently.'
    else:
        response = 'Files open in the system currently: \n'
        count = 0
        for i in open_file_table.keys():
            count += 1
            response += str(count) + '. ' + open_file_table[i][0] + ',  Mode: ' +  str(open_file_table[i][1]) + ', Blocks in memory: ' + str(i.file_blocks) + '\n'
    
    return response

def get_node_from_addr(addr, node):
    a = None
    for i in node.children:
        if addr[0] == i.name:
            if len(addr) < 2:
                return i
            else:
                a = get_node_from_addr(addr[1:], i)
    return a


class TreeNode:
    def __init__(self, name, type="dir"):
        self.name = name
        self.children = []
        self.parent = None
        self.type = type
        self.file_blocks = []

    def add_child(self, child):
        child.parent = self
        self.children.append(child)

    def get_level(self):
        level = -1
        p = self.parent
        while p:
            level += 1
            p = p.parent
        return level

    def print_tree(self):
        spaces = ' ' * self.get_level() * 3
        prefix = spaces + '|__' if self.parent else ''
        print(prefix + self.name)
        if self.children:
            for child in self.children:
                child.print_tree()

# change added
    def heirarchy(self, response):
        spaces = ' ' * self.get_level() * 3
        prefix = spaces + '|__' if self.parent else ''
        if self.type == 'file':
            response +=  prefix + self.name + " Blocks: " + str(self.file_blocks) +'\n'
        else:            
            response += prefix + self.name + '\n'
        if self.children:
            for child in self.children:
                response = child.heirarchy(response)
        return response

    

    def ls(self):
        str = "Empty Folder" if len(self.children) == 0 else ""
        brek = 0
        for i in self.children:
            brek += 1
            if i.type == "file":
                str += "FILE: " + i.name + "    "
            else:
                str += "DIR: " + i.name + "    "
            if brek % 5 == 0:
                str += "\n"
        return str

    def pwd(self):
        str = self.name
        p = self.parent
        while p:
            str = p.name + "/" + str
            p = p.parent
        str = str + "/"
        return str


def update_structures(root):
    memory = [root, blocks]
    with open('mem.dat', 'wb') as out:
        pickle.dump(memory, out)



def move_file(current_node, arg1, arg2):
    node = find_node(current_node, arg1)
    if node[1] == 1:
        addr = arg2.split('/')
        for i in addr:
            if i == '':
                addr.remove(i)
        if len(addr) > 1:
            dir_node = get_node_from_addr(addr[1:], root)
        elif len(addr) == 1 and addr[0] == "E:":
            dir_node = root

        if dir_node:
            dir_node.add_child(node[0])
            current_node.children.remove(node[0])
        else:
            print("Error: Invalid destination path.")
    else:
        print(f"File '{arg1} does not exist in this directory.'")


def find_node(current_node, arg):
    for i in current_node.children:
        if arg == i.name:
            if i.type == 'file':
                return [i, 1]
            else:
                return [i, 2]
    return [None, -1]

def input_text():
    a = input("Would you like to manually input data or copy it from an already created text file?\nEnter m to enter manually, c to copy from a file: ")
    if a == 'm':
        data = input("Please Input your data. As this is NOT a text editor, enter \\n where you intend to add a newline:\n")
        data = data.split("\\n")
        data = '\n'.join(data)
        print(len(data))
        return data

    else:
        path = input("Enter the file path which contains your content: ")

        if os.path.isfile(path):
            with open(path) as file:
                data = file.readlines()
            fdata = ''.join(data)
            return fdata
        else:
            print("Error: The given path to file is invalid!")
            return None


def view_file(current_node, arg):
    data = ''
    node = find_node(current_node, arg)
    if node[1] == 1:
        for i in node[0].file_blocks:
            data += blocks[i]
    else:
        return None
    return data

def copy_to_file(current_node, arg, arg2):
    f1 = find_node(current_node, arg)
    f2 = find_node(current_node, arg2)

    if f1[1] == 1 and f2[1] == 1:
        f1_data = view_file(current_node, arg)

        for i in f2[0].file_blocks:
            deleteBlock(i)
        f2[0].file_blocks = allocateBlock(f1_data)
        update_structures(root)
        return 0

    elif f1[1] != 1:
        return 1
    else:
        return 2


def truncate(current_node, arg, arg2):
    node = find_node(current_node, arg)
    f_data = ''
    if node[1] == 1:
        if node[0] in open_file_table.keys():
            data = view_file(current_node, arg)
            size = int(arg2)
            for i in node[0].file_blocks:
                deleteBlock(i)
            node[0].file_blocks = allocateBlock(data[:size])
        else:
            return -1
    else:
        return f"File '{arg}' does not exist."

def remove_file_or_directory(current_node, arg):
    node = find_node(current_node, arg)
    if node[0] not in open_file_table.keys():
        if node[0]:
            if node[1] == 2:
                for i in node[0].children:
                    if i.type == 'file':
                        for b in i.file_blocks:
                            deleteBlock(b)

            if node[1] == 1:
                for b in node[0].file_blocks:
                    deleteBlock(b)
            
            current_node.children.remove(node[0])
            update_structures(root)
        else:
            return "Error: No Such directory or file exists within this directory."
    elif node[0] in open_file_table.keys():
        return "Error: File is Open. Please close the file to remove it"
    


def start(current_node, root_node, user_command, userInfo):
    command = " ".join(user_command.split())
    a = command.split(' ')
    end = 0
    response = ''
    # current_node.pwd() + ">" + user_command + "\n"

    if a[0] == "pwd":
        response += current_node.pwd() + '\n'
    elif a[0] == "man":
        if len(a) == 1:
            with open('readme.txt', 'r') as manual:
                d = manual.readlines()
            d = ''.join(d)
            response += d
        elif len(a) == 2:
            if a[1] in manual_dict.keys():
                response += f'\nManual of command {a[1]}:\n' + manual_dict[a[1]] + '\n'
            else:
                response += (f'Command {a[1]} does not exist.')

    elif a[0] == "ls":
        response += current_node.ls()

    elif a[0] == "cd":
        try:
            if a[1] != "..":
                node = find_node(current_node, a[1])
                if node[1] == 2:
                    current_node = node[0]
                else:
                    response += (f"Error: Directory '{a[1]}' doesn't exist.")
            else:
                if current_node.parent:
                    current_node = current_node.parent
        except IndexError:
            response += "Error: No directory specified for 'cd' command."
        except Exception:
            print("An unknown error has occurred.")
            response += "An unknown error has occurred."

    elif a[0] == 'freemem':
        response += (f"\nTotal Blocks in memory: 1000\nFree Blocks: {len(blocks['freeBlocks'])}\n\n {show_open_files()}\n")


    elif a[0] == "mkdir":
        if len(a) == 2:
            dup = find_node(current_node, a[1])
            if not dup[0]:
                current_node.add_child(TreeNode(a[1]))
            else:
                if dup[1] == 1:
                    response += ("A file with this name already exists.")
                elif dup[1] == 2:
                    response += ("A directory with this name already exists.")
        else:
            response += ("Error: Invalid number of arguments with 'mkdir' command.")
        update_structures(root_node)

    elif a[0] == "mv":
        try:
            move_file(current_node, a[1], a[2])
        except IndexError:
            response += ("Invalid number of arguments.")
        update_structures(root_node)

    elif a[0] == 'copy':
        try:
            ret = copy_to_file(current_node, a[1], a[2])
            if ret == 0:
                response += f"Content copied from {a[1]} to {a[2]}."
            elif ret == 1:
                response += f"File {a[1]} does not exist in this directory."
            else:
                response += f"File {a[2]} does not exist in this directory."
        except:
            response += "Error: Invalid number of arguments with 'copy' command."

    elif a[0] == "touch":
        if len(a) == 2:
            try:
                dup = False
                for i in current_node.children:
                    if a[1] == i.name:
                        dup = True
                        break
                if not dup:
                    file_node = TreeNode(a[1], 'file')
                    current_node.add_child(file_node)
                    response += "File created!"
                else:
                    response += "Error: Filename already exists."
            except Exception:
                response += "An unknown error has occured."
            update_structures(root_node)
        else:
            response += "Error: Invalid number of arguments with 'touch' command."


    elif a[0] == "write_to_file":
        try:
            command = user_command.split('"')
            if len(command) == 3:
                new_data = command[1]
                command.remove(command[1])
                command = ''.join(command).split()
                filename =  command[1]
                file_node = find_node(current_node, filename)
                if file_node[1] == 1:
                    if file_node[0] in open_file_table.keys():
                        if open_file_table[file_node[0]][1] == 'w':
                            data = view_file(current_node, filename)
                            if len(command) == 2:
                                for i in file_node[0].file_blocks:
                                    deleteBlock(i)
                                file_node[0].file_blocks = allocateBlock(new_data)
                            elif len(command) == 3:
                                f_data = data[:int(command[2])] + new_data
                                for i in file_node[0].file_blocks:
                                    deleteBlock(i)
                                file_node[0].file_blocks = allocateBlock(f_data)
                            else: 
                                raise IndexError
                        else:
                            response += f'File {filename} is not open in write mode. Close it and open it in write mode to continue.'    
                        update_structures(root_node)
                    else:
                        response += f'File {filename} is not open in memory! Open it to write data to it.'
                else:
                    response += f'File {filename} does not exist in this directory.'        
        except IndexError:
            response += ("Error: Invalid number of arguments with 'write_to_file' command.")
        
    elif a[0] == "read_from_file":
        try:
            file_node = find_node(current_node, a[1])
            
            if file_node[0] in open_file_table.keys():
                if open_file_table[file_node[0]][1] == 'r':
                    data = view_file(current_node, a[1])

                    if data:
                        if len(a) == 2:
                            response += data
                        elif len(a) == 4:
                            response += data[int(a[2]):int(a[3])]
                        else:
                            raise IndexError   
                    if data == '' and data != None:

                        response += ("File is empty!")
                else:
                    response += f'File {filename} is not open in read mode. Close it and open it in read mode to continue.'
            elif file_node[1] == 1:
                response += f'File {a[1]} is not open in memory.'
            else:
                response += f'File {a[1]} does not exist in this directory.'
    
        except IndexError:
            response += ("Error: Invalid number of arguments with 'read_from_file' command.")
    
    # 0, not open, 1 in read mode, 2 in write mode, 3: just got closed.
    elif a[0] == 'open':
        try:
            file_node = find_node(current_node, a[1])[0]
            if a[2] == 'w' or a[2] == 'r':
                if file_node != None:
                    if file_node not in open_file_table.keys():
                        if len(users[userInfo]) < 5:
                            open_file_table[file_node] = [current_node.pwd() + a[1] , a[2], [userInfo]]
                            response += f'File "{a[1]}" is now open in memory.\n' + show_open_files() # show memory map
                            users[userInfo].append(file_node)
                            if a[2] == 'w':
                                end = 1
                            else:
                                end = 2
                        else:

                            response += f'User {userInfo} has reached the limit for opening 5 files.'
                    else:
                        response += f'File "{a[1]}" is already Open in memory.\n' + show_open_files()
                else:
                    response += f'File {a[1]} does not exist in this directory.'
            else:
                response += 'You can only open in read mode "r" or write mode "w".'
                
        except IndexError:
            response += ("Error: Invalid number of arguments with 'open' command.")

    elif a[0] == 'close':
        try:
            file_node = find_node(current_node, a[1])
            if file_node[0] != None and file_node[1] == 1:
                if file_node[0] in open_file_table.keys():
                    userfileList = users[userInfo]
                    userfileList.remove(file_node[0])
                    del open_file_table[file_node[0]]
                    response += f'File {a[1]} is now closed.\nOpen File Table:\n' + show_open_files() + '\n\n'
                    end = 3
                else:
                    response += f'File "{a[1]}" is not open in memory.\n'
            else:
                response += f'File {a[1]} does not exist in this directory.'
        except:
            response += ("Error: Invalid number of arguments with 'close' command.")
    
    elif a[0] == "rm":
        try:
            
            reply = remove_file_or_directory(current_node, a[1])
            if (reply):
                response += reply
            update_structures(root)
        except IndexError:
            response += ("Error: No filename or directory was specified.")

    elif a[0] == "trunc":
        try:
            re = truncate(current_node, a[1], a[2])
            if re == -1:
                response += f'File {a[1]} is not open in memory. Please open it to truncate it'
            elif re:
                response += re   
            else:
                response += ('Done!')
            update_structures(root)
        except IndexError:
            response += ("Error: Invalid number of arguments with trunc command.")

    elif a[0] == "map":
        response += root_node.heirarchy('') + '\nOpen File Table:\n' + show_open_files() + '\n'
        

    else:
        response += (f"Error: Command '{a[0]}' does not exist in this directory.")

    return [current_node, end, response]

try:
    with open('mem.dat', 'rb') as inp:
        memory = pickle.load(inp)
        root = memory[0]
        blocks = memory[1]
    
except:
    print("\nWarning: Your mem.dat file is not present! New file will be created.")
    root = TreeNode('E:')
    blocks = []
    for i in range(1000):
        blocks.append(i)

    blocks = {
        "freeBlocks":blocks,
        }  

# print("\nEnter 'man' command to view the manual for this terminal.\nTotal Blocks in memory: 1000\nBlocks available in the memory: ",len(blocks['freeBlocks']), "\nSize of 1 block: 10 characters.\n")




# print('E:/>', end='')







ServerSideSocket = socket.socket()
host = '127.0.0.1'
port = 2004
ThreadCount = 0
try:
    ServerSideSocket.bind((host, port))
except socket.error as e:
    print(str(e))
print('Socket is listening..')
ServerSideSocket.listen(5)
def multi_threaded_client(connection):
    connection.send(str.encode('Welcome to the file system! Please enter your name: '))
    name = connection.recv(2048)
    name = name.decode('utf-8')
    users[name] = []
    print(f'User {name} has connected!')
    print(users)
    info = start(root,root,'man','')
    connection.send(str.encode(root.pwd()))
    while True:
        
        data = connection.recv(10240)
        dataDecoded = data.decode('utf-8')
        info = start(info[0], root, dataDecoded.strip(), name)
        response = info[2] + '\n' + info[0].pwd() + '>'
        if not data or dataDecoded == 'exit':
            if dataDecoded == 'exit':
                response = 'Exiting.'
            print(name + ' disconnected!')
            for i in users[name]:
                del(open_file_table[i])
            del(users[name])
            print(users)
            update_structures(root)
            break
        
        connection.sendall(str.encode(response))
    connection.close()
while True:
    Client, address = ServerSideSocket.accept()
    print('Connected to: ' + address[0] + ': ' + str(address[1]))
    start_new_thread(multi_threaded_client, (Client, ))
    ThreadCount += 1
    print('Thread Number: ' + str(ThreadCount))
ServerSideSocket.close()

