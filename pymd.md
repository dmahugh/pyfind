#pymd documentation
    Generate Markdown documentation from Python module.  
      
    cli() -----------------> Handle command-line arguments.  
    generate_markdown() ---> Generate Markdown documentation for a module.  
    no_extension() --------> Remove .py extension from module name.
##generate_markdown
    Generate Markdown documentation for specified module.  
      
    module = name of the module (may also be passed as a command line argument)  
      
    Creates a module.md file with documentation based on the docstrings in  
    module.py. Overwrites module.md if it already exists.  
      
    Special case: if the string 'internal' surrounded by <> occurs in a  
    function's docstring it will be displayed with a smaller heading in  
    the module.md output file.