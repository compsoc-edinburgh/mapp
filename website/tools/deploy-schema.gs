// original source: https://gist.github.com/mderazon/9655893#file-export-to-csv-gs
// original post: https://www.drzon.net/posts/export-all-google-sheets-to-csv/
// original author: author: Michael Derazon

function onOpen() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var csvMenuEntries = [
    { name: "Mapp: deploy schema (all)", functionName: "deployAll" },
    { name: "Mapp: deploy schema (this sheet)", functionName: "deployThis"},
    { name: "Mapp: drop room (this sheet)", functionName: "dropThis"}
  ];
  ss.addMenu("Better Informatics", csvMenuEntries);
  
  var DEV_csvMenuEntries = [
    { name: "[DEV] Mapp: deploy schema (all)", functionName: "DEV_deployAll" },
    { name: "[DEV] Mapp: deploy schema (this sheet)", functionName: "DEV_deployThis"},
    { name: "[DEV] Mapp: drop room (this sheet)", functionName: "DEV_dropThis"}
  ];
  ss.addMenu("[DEV] Better Informatics", DEV_csvMenuEntries);
};

function DEV_deployThis() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var s = ss.getActiveSheet();
  deploySheets([s], false, false, true);
}

function DEV_dropThis() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var s = ss.getActiveSheet();
  deploySheets([s], false, true, true);
}

function DEV_deployAll() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheets = ss.getSheets();
  deploySheets(sheets, true, false, true);
}

function deployThis() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var s = ss.getActiveSheet();
  deploySheets([s], false, false);
}

function dropThis() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var s = ss.getActiveSheet();
  deploySheets([s], false, true);
}

function deployAll() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheets = ss.getSheets();
  deploySheets(sheets, true, false);
}

function deploySheets(sheets, resetAll, dropOnly, DEV_ENDPOINT) {
  var machines = []
  for (var i = 0; i < sheets.length; i++) {
    var sheet = sheets[i];
    if (sheet.isSheetHidden()) {
      Logger.log("sheet skipped: " + sheet.getName())
      continue;
    }
    Logger.log("sheet happening: " + sheet.getName())

    // convert all available sheet data to csv format
    var csvFile = convertRangeToCsvFile_(sheet);
    machines.push({name: sheet.getName(), csv: csvFile})
  }

  var options = {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify({
      'callback-key': PropertiesService.getScriptProperties().getProperty("authorised-key"),
      machines: machines,
      resetAll: resetAll,
      dropOnly: dropOnly,
    }),
    muteHttpExceptions: true
  };
  
  var urlpath = 'mapp';
  if (DEV_ENDPOINT) {
    urlpath += "-dev";
  }

  var r = UrlFetchApp.fetch("https://"+urlpath+".betterinformatics.com/api/update_schema", options)
  Logger.log(r)
  Browser.msgBox(r)
}

function convertRangeToCsvFile_(sheet) {
  // get available data range in the spreadsheet
  var activeRange = sheet.getDataRange();
  try {
    var data = activeRange.getValues();
    var csvFile = undefined;

    // loop through the data in the range and build a string with the csv data
    if (data.length > 1) {
      var csv = "";
      for (var row = 0; row < data.length; row++) {
        for (var col = 0; col < data[row].length; col++) {
          if (data[row][col].toString().indexOf(",") != -1) {
            data[row][col] = "\"" + data[row][col] + "\"";
          }
        }

        // join each row's columns
        // add a carriage return to end of each row, except for the last one
        if (row < data.length - 1) {
          csv += data[row].join(",") + "\r\n";
        }
        else {
          csv += data[row];
        }
      }
      csvFile = csv;
    }
    return csvFile;
  }
  catch (err) {
    Logger.log(err);
    Browser.msgBox(err);
  }
}
