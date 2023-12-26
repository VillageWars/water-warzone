import sys
def execute(self, text):
    argv = text.split(' ')
    command = argv[0]
    if command == 'exec':
        server = self.server
        try:
            exec(' '.join(argv[1:]))
            self.Send({'action':'msg', 'msg': 'Executed code'})
        except SyntaxError as err:
            self.Send({'action':'msg', 'msg': 'SyntaxError: ' + err})
        except Exception as err:
            self.Send({'action':'msg', 'msg': 'Exception: ' + err})
    elif command == 'restart':
        self.Send({'action':'msg', 'msg': 'Restarting'})
        sys.exit()
    elif command == 'say':  # Prank
        for p in self.server.players:
            p.Send({'action':'prank', 'msg':' '.join(argv[1:])})
    
        
