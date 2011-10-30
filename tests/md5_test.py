import os, sys, time, hashlib
from progressbar import ProgressBar, Bar, ETA

def md5sum(f, block_size=2 ** 20):
    md5 = hashlib.md5()
    # check if file was moved/deleted before opening
    if not os.path.isfile(f):
        return(None)

    widgets = [Bar(left="[", right="]", marker="="), ' ', ETA()]
    # set maxval to the total size of the file, this is 
    # so progressbar can calc the eta/percentage completed of hash check
    bar = ProgressBar(widgets=widgets, maxval=os.stat(f).st_size).start()

    try:
        with open(f, "rb") as fp:
            bytes_read = 0
            while True:
                # check if file has moved/deleted during md5 creation
                if not os.path.isfile(f):
                    return(None)
                data = fp.read(block_size)
                if not data:
                    break
                md5.update(data)

                bytes_read += len(data)
                bar.update(bytes_read)

    except IOError:
        # another failsafe in case open() throws error
        return(None)

    bar.finish()
    return(md5.hexdigest())

def main():
    f = sys.argv[-1]
    start = time.time()
    print(md5sum(f))
    print("Time Elapsed: {0} seconds".format(time.time() - start))

if __name__ == '__main__':
    main()
