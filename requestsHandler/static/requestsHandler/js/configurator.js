$(document).ready(function(){
$.get("/getSchema", function( schema ) {
    console.log(JSON.parse(schema));
    // Set default options
    JSONEditor.defaults.options.theme = 'bootstrap3';
    
    // Initialize the editor
    var editor = new JSONEditor(document.getElementById("editor_holder"),{
      schema: {
          type: "object",
          properties: {
              name: { "type": "string" }
          }
      }
    });
    
    // Set the value
    editor.setValue({
        name: "John Smith"
    });
    
    // Get the value
    var data = editor.getValue();
    console.log(data.name); // "John Smith"
    
    // Validate
    var errors = editor.validate();
    if(errors.length) {
      // Not valid
    }
    
    // Listen for changes
    editor.on("change",  function() {
      // Do something...
    }); 
});
});