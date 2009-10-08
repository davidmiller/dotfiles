#!/usr/bin/env python
""" Syncs dotfiles across machines """
import logging
import os
import sqlite3
import subprocess
import StringIO
import sys
import argparse

class Dotfiles:
    """ Main Dotfiles class """


    def init( self ):
        """ Initialise the dotfiles dir, repo, db """
        self.mk_dotfiles_dir()
        self.mk_repo()
        self.mk_db()
        print """ Created .dotfiles directory, repo at ~/.dotfiles"""
        return True


    def mk_dotfiles_dir( self ):
        """ Creates the .dotfiles dir """
        os.mkdir( self.dotfiles_dir )
        return os.path.isdir( self.dotfiles_dir )


    def mk_repo( self ):
        """ Creates the dotfiles git repo """        
        self.cwd = os.getcwd()
        os.chdir( self.dotfiles_dir )
        gitout = StringIO.StringIO()
        git_init_proc = subprocess.Popen( ['git', 'init'],
                                          stdout = subprocess.PIPE )
        init_logger.debug( git_init_proc.stdout.read() )
        ignore_fh = open( '.gitignore', 'wb' )
        ignore_fh.write( 'dotfiles.db\n' )
        ignore_fh.close()
        git_add_args = ['git', 'add', '.' ]
        git_add_proc = subprocess.Popen( git_add_args,
                                            stdout = subprocess.PIPE )
        init_logger.debug( git_add_proc.stdout.read() )                           
        git_commit_args = [ 'git', 'commit', '-a' , '-m',
                           'Initial Commit']
        git_commit_proc = subprocess.Popen( git_commit_args,
                                            stdout = subprocess.PIPE )
        init_logger.debug( git_commit_proc.stdout.read() )
        return os.path.isdir( self.repo_dir )


    def mk_db( self ):
        """ Create the dotfiles database """
        self.db_conn()
        self.c.execute(''' create table files
                           ( file_id INTEGER PRIMARY KEY, host_id real, name text,
                              mod text, version, real, origin, text ) ''')
        self.c.execute(''' create table hosts
                           ( host_id INTEGER PRIMARY KEY, pubkey text ) ''')
        self.c.execute(""" insert into hosts( host_id, pubkey )
                           VALUES( NULL, '""" + self.pubkey + "' )" )
        self.conn.commit()
        self.c.close()

    
    def add( self ):
        """ Start tracking a dotfile """
        add_logger.debug( 'Adding ' + self.args.file )
        if not os.path.isdir( self.dotfiles_dir ):
            add_logger.debug( 'No .dotfiles dir' )
            self.init()
        else:
            add_logger.debug( 'Found .dotfiles dir' )

    
    def sync( self ):
        """ Syncs existing tracked dotfiles """
        print 'SYNC'


    def db_conn( self ):
        """ Connects to the database & stores cursor """
        db_loc = os.path.join( self.dotfiles_dir, 'dotfiles.db' )
        init_logger.debug( 'Database location: ' + db_loc )
        self.conn = sqlite3.connect( db_loc )
        self.c = self.conn.cursor()        


    def __init__( self, args=None ):
        """ Constructs the dotfiles Class """
        self.args = args
        home = os.environ['HOME']
        pubkey_loc = os.path.join( home, '.ssh/id_dsa.pub' )
        # Check for required elements
        if not os.path.isfile( pubkey_loc ):
            print """No Public Key found at ~/.ssh/id_dsa.pub either specify
            alternate Public Key location with --public-key or generate one
            with ssh-keygen -t dsa"""
            sys.exit()

        pubkey_fh = open( pubkey_loc )
        self.pubkey = pubkey_fh.read()
        pubkey_fh.close()
        
        self.dotfiles_dir = os.path.join( home, '.dotfiles' )
        self.repo_dir = os.path.join( self.dotfiles_dir, '.git' )
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

    # dotfiles init commands
    parser_init = subparsers.add_parser( 'init', help = 'Initialise dotfiles' )
    parser_init.set_defaults( func = 'init' )

    # Adding dotfiles commands
    parser_add = subparsers.add_parser( 'add', help = 'Start tracking a dotfile' )
    parser_add.add_argument( 'file',
                             help='Location of the flie to track' )
    parser_add.set_defaults( func = 'add' )

    # Syncing dotfiles commands
    parser_sync = subparsers.add_parser( 'sync',
                                         help = 'manually sync dotfiles' )
    parser_sync.set_defaults( func = 'sync' )

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

    #Initialise the object
    dotfiles = Dotfiles( args )
