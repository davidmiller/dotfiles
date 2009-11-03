#!/usr/bin/env python
""" Syncs dotfiles across machines """
import logging
import os
import re                      
import shutil
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
        # This is where we create the local & remote repositories.
        # commit & push to the remote via the repo ruby program
        self.mk_repo()
        self.mk_db()
        print """ Created .dotfiles directory, repo at ~/.dotfiles"""
        return True


    def mk_dotfiles_dir( self ):
        """ Creates the .dotfiles dir """
        try
            os.mkdir( self.dotfiles_dir )
        except OSError:
            print "dotfiles directory already exists, skipping"
        return os.path.isdir( self.dotfiles_dir )


    def mk_repo( self ):
        """ Creates the dotfiles git repo """        
        os.chdir( self.dotfiles_dir )
        ignore = 'dotfiles.db'
        repo_args = [ 'repo' 'init', 'mydotfiles', '--ignore', ignore ]
        repo_proc = subprocess.Popen( repo_args, stdout = subprocess.PIPE )
        init_logger.debug( repo_proc.stdout.read() )        
        return os.path.isdir( self.repo_dir )


    def mk_db( self ):
        """ Create the dotfiles database """
        self.db_conn()
        self.c.execute( ''' create table files
                           ( file_id INTEGER PRIMARY KEY, host_id INTEGER, name text,
                             origin, text ) ''')
        self.c.execute( ''' create table hosts
                           ( host_id INTEGER PRIMARY KEY, pubkey text ) ''')
        self.c.execute( 'create table github ( user text, token text )' )
        self.c.execute( """ insert into hosts( host_id, pubkey )
                            VALUES( NULL, '""" + self.pubkey + "')" )
        self.c.execute( """ insert into github ( user, token )
                            VALUES ( ?, ?) """, ( self.git_user, self.git_token ) )
        self.conn.commit()
        self.c.close()

    
    def add( self ):
        """ Start tracking a dotfile """
        add_logger.debug( 'Adding ' + self.args.file )

        # Locate the file
        if not os.path.isdir( self.dotfiles_dir ):
            add_logger.debug( 'No .dotfiles dir' )
            self.init()
        else:
            add_logger.debug( 'Found .dotfiles dir' )
            if os.path.isfile( self.args.file ):
                if self.args.file[:1] == '/':
                    file_loc = self.args.file
                else:
                    file_loc = os.path.join ( os.getcwd(), self.args.file )
            else:                
                file_loc = os.path.join( os.environ['HOME'], self.args.file )
                if os.path.isfile( file_loc ):                    
                    add_logger.debug( self.args.file + ' found in home dir' )
                else:
                    print  self.args.file + ' not found - please check the location \
and filename are correct and try again'
                    sys.exit()

        # store the file in the database            
        file_name_RE = re.compile( r'^.+/(.+)$' )
        file_name = file_name_RE.search( file_loc ).groups()[0]
        self.db_conn()
        host_sql = "select host_id from hosts where pubkey = '" + self.pubkey + "'"
        host_id = int( self.c.execute( host_sql ).fetchall()[0][0] )
        insert_values = ( host_id, file_name, file_loc ) 
        self.c.execute(""" insert into files (file_id, host_id, name, origin)
                           VALUES( NULL, ?, ?, ? )""", insert_values)
        self.conn.commit()

        # relocate original file
        shutil.move( file_loc, self.dotfiles_dir )
        os.symlink( os.path.join( self.dotfiles_dir, file_name ) , file_loc )

    
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
        self.cwd = os.getcwd()
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
        init_logger.debug( 'dotfiles_dir: ' + self.dotfiles_dir )
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
#    add_logger = genlog.gen_log( 'add', LOG_FILENAME )    

    logformat = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter( logformat )
    file_handler = logging.FileHandler( LOG_FILENAME )
    file_handler.setFormatter( formatter )
    file_handler.setLevel( logging.ERROR )
    console_handler = logging.StreamHandler()
    console_handler.setFormatter( formatter )
    console_handler.setLevel( logging.DEBUG )

    sync_logger = logging.getLogger( 'sync' )
    init_logger = logging.getLogger( 'init' )    
    sync_logger.setLevel( logging.DEBUG )
    init_logger.setLevel( logging.DEBUG )
    init_logger.addHandler( file_handler )
    sync_logger.addHandler( file_handler )
    init_logger.addHandler( console_handler )
    sync_logger.addHandler( console_handler )

    #Initialise the object
    dotfiles = Dotfiles( args )
