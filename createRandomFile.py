import os
import random
import string
import sys
def randomString(stringLength=50000):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))

def createFile(fileName, size):
    with open(fileName, 'w') as f:
        f.write(randomString(size))

def main():
    num_of_files = int(sys.argv[1])
    for i in range(1, num_of_files+1):
        fileName = 'randomFile' + str(i) + '.txt'
        size = 1024 * 1024 * 2 # 2MB
        createFile(fileName, size)
        print('Created file:', fileName)

if __name__ == '__main__':
    main()