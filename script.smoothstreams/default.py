import sys

if __name__ == '__main__':
    arg = None
    if len(sys.argv) > 1: arg = sys.argv[1] or False
    if arg == 'REFRESH_SCHEDULE':
        from lib import smoothstreams
        smoothstreams.Schedule.sscachejson(force=True)
    elif arg == 'ABOUT':
        from lib import util
        util.about()
    elif arg == 'DOWNLOAD_CALLBACK':
        from lib.smoothstreams import player
        player.downloadCallback(sys.argv[2])
    else:
        from ssmain import main
        main()