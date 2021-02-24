import subprocess

# -------------------------------------------------------------------------
def args_test(parser):
    pass

def cmd_test(args):
    """Run preconfigured test"""
    try:
        subprocess.run(['/usr/local/bin/test-mkt.sh'], check=True)
    except subprocess.CalledProcessError:
        sys.exit("================= TEST FAILED =================")

    print("================= TEST PASSED =================")
