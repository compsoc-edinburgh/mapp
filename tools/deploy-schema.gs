// original source: https://gist.github.com/mderazon/9655893#file-export-to-csv-gs
// https://www.drzon.net/posts/export-all-google-sheets-to-csv/

/*
 * script to export data in all sheets in the current spreadsheet as individual csv files
 * files will be named according to the name of the sheet
 * author: Michael Derazon
*/

function onOpen() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var csvMenuEntries = [{ name: "Mapp: deploy schema", functionName: "saveAsCSV" }];
  ss.addMenu("Better Informatics", csvMenuEntries);
};

function saveAsCSV() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheets = ss.getSheets();
  // create a folder from the name of the spreadsheet
  //var folder = DriveApp.createFolder(ss.getName().toLowerCase().replace(/ /g,'_') + '_csv_' + new Date().getTime());
  //var blobs = [];
  var machines = []
  for (var i = 0; i < sheets.length; i++) {
    var sheet = sheets[i];
    if (sheet.isSheetHidden()) {
      Logger.log("sheet skipped: " + sheet.getName())
      continue;
    }
    Logger.log("sheet happening: " + sheet.getName())
    // append ".csv" extension to the sheet name
    fileName = sheet.getName() + ".csv";
    // convert all available sheet data to csv format
    var csvFile = convertRangeToCsvFile_(fileName, sheet);
    // create a file in the Docs List with the given name and the csv data
    //folder.createFile(fileName, csvFile);
    //blobs.push(Utilities.newBlob(csvFile, "application/zip", fileName))

    machines.push({ name: sheet.getName(), csv: csvFile })
  }

  var options = {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify({
      'callback-key': PropertiesService.getScriptProperties().getProperty("authorised-key"),
      machines: machines,
    }),
    muteHttpExceptions: true
  };
  
  var r = UrlFetchApp.fetch('https://mapp.betterinformatics.com/api/update_schema', options)
  Logger.log(r)
  Browser.msgBox(r)

  //var f = DriveApp.createFile(Utilities.zip(blobs, 'mapp_dice_rooms.zip'))
  //f.setSharing(DriveApp.Access.ANYONE, DriveApp.Permission.VIEW)


  //Browser.msgBox("Download is ready", "", null)
  //Browser.msgBox('Files are waiting in a folder named ' + folder.getName());

}

function convertRangeToCsvFile_(csvFileName, sheet) {
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
