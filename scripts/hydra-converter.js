var fs = require('fs');

if (process.argv[2]) {
  var record = process.argv[2].replace(/"/g, '\'').replace(/\+/g, '%2B').replace(/&/g, '%26');
  console.log("\n\nOUTPUT:\n\n");
  console.log(record);
}

