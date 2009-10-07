#!/usr/bin/env python
""" Syncs dotfiles across machines """
import logging
import os
import subprocess
import StringIO
import argparse

class Dotfiles:
    """ Main Dotfiles class """


    def init( self ):
        os.mkdir( self.dotfiles_dir )
        self.cwd = os.getcwd()
        os.chdir( self.dotfiles_dir )
        gitout = StringIO.StringIO()
        git_init_proc = subprocess.Popen( ['git', 'init'], stdout = subprocess.PIPE )
        init_logger.debug( git_init_proc.stdout.read() )

    def add( self ):
        """ Start tracking a dotfile """
        if not os.path.isdir( self.dotfiles_dir ):
            add_logger.debug( 'No .dotfiles dir' )
            self.init()
        else:
            add_logger.debug( 'Found .dotfiles dir' )

    
    def sync( self ):
        """ Syncs existing tracked dotfiles """
        print 'SYNC'


    def __init__( self, args=None ):
        self.args = args
        home = os.environ['HOME']
        dotfiles_dir = os.path.join( home, '.dotfiles' )
        self.dotfiles_dir = dotfiles_dir

        if self.args.func:            
            fn = getattr( self, args.func )
            fn()


if __name__ == '__main__':


    # Set arguments
    program = 'dotfiles'
    parser = argparse.ArgumentParser( prog = program )
    parser.add_argument( '--debug',
                         action='store_true',
                         help='Turn on debugging notices')
    subparsers = parser.add_subparsers( help = 'sub command help' )

    parser_sync = subparsers.add_parser( 'sync',
                                         help = 'manually sync dotfiles' )
    parser_sync.set_defaults( func = 'sync' )

    parser_add = subparsers.add_parser( 'add', help = 'Start tracking a dotfile' )
    parser_add.add_argument( 'file',
                             help='Location of the flie to track' )
    parser_add.set_defaults( func = 'add' )
    
    args = parser.parse_args()



    #  Define logging behaviour
    LOG_FILENAME = '.dotfiles.log'
    if args.debug:
        console_level = logging.DEBUG
    else:
        console_level = logging.ERROR

    add_logger = logging.getLogger( 'add' )
    sync_logger = logging.getLogger( 'sync' )
    init_logger = logging.getLogger( 'init' )    

    logformat = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter( logformat )

    add_logger.setLevel( logging.DEBUG )
    sync_logger.setLevel( logging.DEBUG )
    init_logger.setLevel( logging.DEBUG )
    
    file_handler = logging.FileHandler( LOG_FILENAME )
    file_handler.setFormatter( formatter )
    file_handler.setLevel( logging.ERROR )
    console_handler = logging.StreamHandler()
    console_handler.setFormatter( formatter )
    console_handler.setLevel( console_level )

    add_logger.addHandler( file_handler )
    init_logger.addHandler( file_handler )
    sync_logger.addHandler( file_handler )
    init_logger.addHandler( console_handler )
    add_logger.addHandler( console_handler )    
    sync_logger.addHandler( console_handler )


    dotfiles = Dotfiles( args )
