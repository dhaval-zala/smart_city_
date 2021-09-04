var queries = "type=*";
// 37.39856 -121.94866 
// 37.39951519999999,-121.9503107
var office = { lat:37.39856 , lon:-121.94866};
var sensorsArray = [];
var algorithms = [];
var algorithmsArray = [];
var algoToSensor = {};
apiHost
  .search(
    "offices",
    "location:[" + office.lat + "," + office.lon + "," + 3000 + "]",
    null
  )
  .then((data) => {})
  .catch((err) => console.log(err));

apiHost
  .search(
   "sensors",
    "(" +
      queries +
      ") and location:[" +
      office.lat +
      "," +
      office.lon +
      "," +
      3000 +
      "]",
    office
  )
  .then((sensor_reply) => {
    console.log("Data", sensor_reply.response);
    $.each(sensor_reply.response, (x, sensor) => {
      var sensor_id = sensor._id;
      var sensor_address = sensor._source.address;
      var algo_name = sensor._source.algorithm;

      if (algoToSensor[algo_name] === undefined) {
        // new algo_name found
        algoToSensor[algo_name] = [sensor_id + " " + sensor_address];
        algorithms.push(algo_name);
      } else {
        algoToSensor[algo_name].push(sensor_id + " " + sensor_address);
      }
    });
    var $inputAlgorithm = $("select[name='algorithm']");

    algorithms.forEach((algorithm) => {
      $inputAlgorithm.append(
        $("<option>", { value: algorithm, html: algorithm })
      );
    });
  })
  .catch((err) => console.log(err));
$("#sensorSelected").prop("disabled", true);
$("#algorithmSelected").change(function () {
  var algo_name = $("#algorithmSelected").find(":selected").text();
  $("#sensorSelected").prop("disabled", false);
  var $inputSensor = $("select[name='sensor']");
  const sensorIds = algoToSensor[algo_name];
  $("#sensorSelected").find("option").not(":first").remove(); //removing previous list
  sensorIds.forEach((sensorId) =>
    $inputSensor.append($("<option>", { value: sensorId, html: sensorId }))
  );
});

/*apiHost
  .search_without_offices(index,"(" +
    queries +
    ")", office)
  .then((sensor_reply) => {
    console.log("Data", sensor_reply.response);
    $.each(sensor_reply.response, (x, sensor) => {
      var sensor_id = sensor._id;

      if (!(sensor_id in sensors)) {
        sensors.push(sensor_id);
      }
      var $inputProduct = $("select[name='sensor']");
      sensors.forEach((sensor) => {
        $inputProduct.append($("<option>", { value: sensor, html: sensor }));
        console.log(sensor);
      });
    });
  })
  .catch((err) => console.log(err));
*/
var myVideo = document.getElementById("currentVideo");
var myRecord = document.getElementById("noRecords");
var errorMsg = document.getElementById("errMsg");
var recordNo = document.getElementById("recordsLength");
var desc = document.getElementById("videoDesc");
function fetchRecordings(startTime, endTime) {
  var sensor_id_with_address = $("#sensorSelected").find(":selected").text();
  var sensor_id = sensor_id_with_address.split(" ")[0];
  console.log("Sensor_id", sensor_id);
  apiHost
    .search(
      "recordings",
      'sensor="' +
        sensor_id +
        '" and time >=' +
        startTime +
        "and time <" +
        endTime,
      office
    )
    .then((recording_reply) => {
      console.log("Recording Response", recording_reply.response);
      // $("#recordsLength").text(
      //   "No of Records  : " + recording_reply.response.length
      // );
      recordNo.style.display = "block";
      if (recording_reply.response.length > 0) {
         
        $("#recordsLength").text(
          "No of Records  : " + recording_reply.response.length
        );
        
        myVideo.style.display = "block";
        myRecord.style.display = "none";

        recording_reply.response.sort(function (a, b) {
          return a._source.time - b._source.time;
        });
        $.each(recording_reply.response, (x, v) => {
          v._source.office = office;

          var time = new Date(v._source.time).toLocaleString();
          var address = "address" in v._source ? v._source.address : "";
          var videoPath = api_host_url(office, "recording/" + v._source.path);
          var imagePath =
            videoPath.replace(/\.mp4$/, ".mp4.png") + "?size=640:360";

          var $inputProduct = $("#imgList");
          const imgStructure =
            $(` <div class="col-12 py-2 imgDiv" id="imgDiv"  data-recording = '${JSON.stringify(
              v
            )}' data-address="${address}"  data-time="${time}" data-video=${videoPath}>
                        <div
                          class="
                            bg-image
                            hover-overlay
                            ripple
                            shadow-1-strong
                            rounded
                          "
                          data-ripple-color="light"
                        >
                          <img
                            src=${imagePath}
                            class="w-100"
                          />
                          <a
                            href="#!"
                            data-mdb-toggle="modal"
                            data-mdb-target="#exampleModal2"
                          >
                            <div
                              class="mask"
                              style="background-color: rgba(251, 251, 251, 0.2)"
                            ></div>
                          </a>
                        </div>
                        <div class="text-left" style="font-size: small">
                          ${address}
                        </div>
                        <div class="text-left" style="font-size: small">
                        ${time}
                        </div>
                      </div>`);
          // $inputProduct.append(imgStructure);
          $inputProduct.append(imgStructure);
        });
      } else {
        var errorCode = AividStatusCodes.NORECORDFOUND;
        console.log(errorCode);
        //  $("#recordsLength").text("No of records are : " + a.length);
        $("#recordsLength").text(getStatusDetails(errorCode).message);
        myVideo.style.display = "none";
        myRecord.style.display = "display";
      }
      // onclick event
      $(".imgDiv").click(function (e) {
        const videoLink = $(this).data("video");
        const videoAddress = $(this).data("address");
        const videoTime = $(this).data("time");
        const recordingInfo = $(this).data("recording");

        console.log("RecordingInfo: ", recordingInfo);
        desc.style.display = "block";
        $("#currentVideo").attr("src", videoLink);
        $("#videoDesc").text(videoAddress + " " + videoTime);

        var page = $("#videoPage video");

        draw_analytics(page, recordingInfo);
        // getVideoPage(recordingInfo);
      });
    })
    .catch((err) => {
      console.log("ERROR", err);
    });
}

$("#fetchRecordingBtn").click(() => {
  $("#imgList").empty();
  var datearray = $("#datetimepicker1").val().split("-");
  var d1 = datearray[1] + "-" + datearray[0] + "-" + datearray[2];
  var t1 = $("#datetimepicker2").val();

  var datearray1 = $("#datetimepicker3").val().split("-");
  console.log(datearray1);
  var d2 = datearray1[1] + "-" + datearray1[0] + "-" + datearray1[2];
  var t2 = $("#datetimepicker4").val();

  var start = new Date(d1 + " " + t1);
  startTimeStamp = start.getTime();

  var end = new Date(d2 + " " + t2);
  endTimeStamp = end.getTime();

  console.log("Date", new Date(startTimeStamp));
  if (startTimeStamp > endTimeStamp) {
     errorMsg.style.display = "block";
     var errorCode = AividStatusCodes.STARTTIMELESSTHANENDTIME;
        console.log(errorCode);
        //  $("#recordsLength").text("No of records are : " + a.length);
    $("#errMsg").text(getStatusDetails(errorCode).message);
    desc.style.display = "none";
    myVideo.style.display = "none";
    myRecord.style.display = "display";
    recordNo.style.display = "none";
      
  }
  else {
       errorMsg.style.display = "none";
    fetchRecordings(startTimeStamp, endTimeStamp);
  }

});



$(function () {
  $("#fetchRecordingBtn").attr("disabled", true);
  $(".form-control").change(function () {
    console.log("Hack : ", $("#sensorSelected").val());
    if (
      $("#datetimepicker1").val() != "" &&
      $("#datetimepicker2").val() != "" &&
      $("#datetimepicker3").val() != "" &&
      $("#datetimepicker4").val() != "" &&
      $("#sensorSelected").val() != null &&
      $("#algorithmSelected").val() != ""
    ) {
         $("#fetchRecordingBtn").attr("disabled", false);
    } else {
      $("#fetchRecordingBtn").attr("disabled", true);
    }
  });
});

$(function () {
  $("#datetimepicker1").datetimepicker({
    format: "DD-MM-YYYY",
  });
  $("#datetimepicker2").datetimepicker({
    format: "LT",
  });

  $("#datetimepicker3").datetimepicker({
    format: "DD-MM-YYYY",
  });
  $("#datetimepicker4").datetimepicker({
    format: "LT",
  });
});

$("input[type='text']").keydown((event) => {
  event.preventDefault();
});

$(".calicon.triggerBtn").click(function () {
  // $("#datetimepicker1").focus();
  $(this).closest("div").find(".form-control.trigger").focus();
});

$(".clockicon.triggerBtn").click(function () {
  $(this).closest("div").find(".form-control.trigger").focus();
});

const AividStatusCodes = {
  ERRORINPROCESS: 100,
  MANDATORYFIELDMISSING: 101,
  ALREADYEXISTS: 102,
  INVALIDUID: 103,
  INCORRECTOTP: 104,
  INVALIDCREDENTIALS: 105,
  INVALIDFIELD: 106,
  USERACCOUNTDOESNOTEXISTS: 107,
  PASSWORDCONFIRMPASSWORDAREDIFFERENT: 108,
  NOUSERRIGHTS: 109,
  SAVEDSUCCESSFULLY: 110,
  GETSUCCESSFULLY: 111,
  UPDATESUCCESSFULLY: 112,
  DELETESUCCESSFULLY: 113,
  NORECORDFOUND: 114,
  CONNECTIVITYERROR: 115,
  RESTRICTEDKEYWORDINENTITYNAME: 116,
  DATABASECONNECTIONLOST: 117,
  USERACCOUNTLOCKED: 118,
  PASSWORDEXPIRED: 119,
  OLDPASSWORDREUSE: 120,
  REQUIREDSTRONGSECURITYFORPASSWORD: 121,
  REQUIREDMEDIUMSECURITYFORPASSWORD: 122,
  USERDELETED: 123,
  RESETPASSWORDFAILED: 124,
  USERPASSWORDCHANGE: 125,
  USERDISABLED: 126,
  DUPLICATEENTRYNOTALLOWED: 127,
  FMANDATORYFIELDMISSING: 128,
  FALREADYEXISTS: 129,
  REQUESTTIMEOUT: 130,
  REQUIREDWEAKSECURITYFORPASSWORD: 131,
  INVALIDIMAGE: 132,
  DELETECONFORMATION: 133,
  EDITCONFORMATION: 134,
  STARTIPANDENDIPDIFFERENT: 135,
  SAMESUBNETINSTARTIPANDENDIP: 136,
  SEARCHISINPROGRESS: 137,
  STARTTIMELESSTHANENDTIME: 138,
  RUNTIMEGREATORTHANCURRENTTIME: 139,
  SELECTCURRENTORFUTUREDATE: 140,
  KPICHANGECONFORMATION: 141,
  ZONEFOREACHSENSORREQUIRED: 142,
  NOTIFICATIONREQFORQUEUEEXCEEDED: 143,
  SELECTUSERFORINSIGHTSSHARING: 144,
  STREAMDISCONNECTED: 145,
  SENSOROFFLINE: 146,
  ERRORRECEIVINGSTREAM: 147,
  ALEASTONEREALTIMENOTIFICATION: 148,
  COUNTERFORSENSORREQUIRED: 149,
  RECORDSAREBEINGFETCHED: 15,
  INVALIDFILEFORMAT: 154,
};
// console.log(getStatusDetails(100).message);
const getStatusDetails = (code) => {
  return statusDetails.find(({ statusCode }) => statusCode === code);
};

const statusDetails = [
  {
    statusCode: 100,
    statusName: "ERRORINPROCESS",
    message: "Error in performing operation. Please try again",
    description: "Generic message, whenever something goes wrong.",
    type: "Error",
  },
  {
    statusCode: 101,
    statusName: "MANDATORYFIELDMISSING",
    message: "Mandatory fields are missing",
    description:
      "whenever any request come to backend in which mandatory field is missing.",
    type: "Error",
  },
  {
    statusCode: 102,
    statusName: "ALREADYEXISTS",
    message: "Duplicate value is not allowed.",
    description: "Whenever user tries to enter duplicate value in any field.",
    type: "Error",
  },
  {
    statusCode: 103,
    statusName: "INVALIDUID",
    message: "Invalid Unique Identification No.",
    description:
      "Whenever user tries to fetch the license details or tries to register with invalid unique Identification No.",
    type: "Error",
  },
  {
    statusCode: 104,
    statusName: "INCORRECTOTP",
    message: "Incorrect OTP",
    description: "Indicates OTP entered by user is incorrect/expired",
    type: "Failure",
  },
  {
    statusCode: 105,
    statusName: "INVALIDCREDENTIALS",
    message: "Invalid Email Address/Mobile No. or Password",
    description: "Indicates that user has invalid credentials while logging in",
    type: "Failure",
  },
  {
    statusCode: 106,
    statusName: "INVALIDFIELD",
    message: "Invalid ",
    description:
      "Whenever user enters invalid value/invalid range in any field\n//<Field Label> : Invalid",
    type: "Error",
  },
  {
    statusCode: 107,
    statusName: "USERACCOUNTDOESNOTEXISTS",
    message: "Account with this Email Address/Mobile No. does'nt exists",
    description:
      "User tries to change the password for an account which doesn't exists using Forgot Password option ",
    type: "Failure",
  },
  {
    statusCode: 108,
    statusName: "PASSWORDCONFIRMPASSWORDAREDIFFERENT",
    message: "Password & Confirm Password both should be same",
    description: "User tries to set/change the password",
    type: "Error",
  },
  {
    statusCode: 109,
    statusName: "NOUSERRIGHTS",
    message: "You do not have required permissions for this operation",
    description:
      "Indicates that current user does not have the required permissions for this operation (Add/Edit/Delete)",
    type: "Information",
  },
  {
    statusCode: 110,
    statusName: "SAVEDSUCCESSFULLY",
    message: "Saved Successfully",
    description: "When configurations done by user are saved successfully.",
    type: "Information",
  },
  {
    statusCode: 111,
    statusName: "GETSUCCESSFULLY",
    description: "Records Fetched Successfully",
    type: "Information",
  },
  {
    statusCode: 112,
    statusName: "UPDATESUCCESSFULLY",
    message: "Saved Successfully",
    description:
      "When configurations changes done by user are saved successfully.",
    type: "Information",
  },
  {
    statusCode: 113,
    statusName: "DELETESUCCESSFULLY",
    message: "Deleted Successfully",
    description: "On successful deletion",
    type: "Information",
  },
  {
    statusCode: 114,
    statusName: "NORECORDFOUND",
    message: "No Records found",
    description:
      "Indicates that no records were found for the specified search/filter criteria.",
    type: "Information",
  },
  {
    statusCode: 115,
    statusName: "CONNECTIVITYERROR",
    message: "Error in connection. Please try later",
    description: "Indicates connectivity error",
    type: "Warning",
  },
  {
    statusCode: 116,
    statusName: "RESTRICTEDKEYWORDINENTITYNAME",
    message: "Restricted Keyword in field values are not allowed.",
    description:
      "When user tries to create an entity with name as any restricted word CON, PRN, AUX, NUL, COM1, COM2, COM3, COM4, COM5, COM6, COM7, COM8, COM9, LPT1, LPT2, LPT3, LPT4, LPT5, LPT6, LPT7, LPT8, and LPT9.",
    type: "Error",
  },
  {
    statusCode: 117,
    statusName: "DATABASECONNECTIONLOST",
    message: "Connection lost with database.",
    description: "Indicates that connection with database lost.",
    type: "Failure",
  },
  {
    statusCode: 118,
    statusName: "USERACCOUNTLOCKED",
    message:
      "Your account has been locked due to maximum failed login attempts. Please contact your administrator",
    description: "When maximum login attempts failed",
    type: "Failure",
  },
  {
    statusCode: 119,
    statusName: "PASSWORDEXPIRED",
    message: "Your password has expired. Please change to login",
    description:
      "Indicates user needs to set new password as password has expired.",
    type: "Failure",
  },
  {
    statusCode: 120,
    statusName: "OLDPASSWORDREUSE",
    message:
      "Last <N> passwords can't be reused as new password as per the Password Reuse Policy.",
    description:
      "Indicates that password is same as one of its old password. N is number of old password which user cannot use to set new password",
    type: "Failure",
  },
  {
    statusCode: 121,
    statusName: "REQUIREDSTRONGSECURITYFORPASSWORD",
    message:
      "New Password must contain 8 characters with at least 1 Uppercase, 1 Lower Case, 1 Numeric (0-9) and 1 Special Character (`~!@#$%^&*()-_=+[]\\{}|;’:”,./<>?)",
    description: "Indicates that Password must contain mandatory characters.",
    type: "Failure",
  },
  {
    statusCode: 122,
    statusName: "REQUIREDMEDIUMSECURITYFORPASSWORD",
    message:
      "New Password must contain 8 characters with at least 1 Alphabet, 1 Numeric (0-9)",
    description: "Indicates that Password must contain mandatory characters.",
    type: "Failure",
  },
  {
    statusCode: 123,
    statusName: "USERDELETED",
    message:
      "Your user account is deleted from system.You will be logged immediately.",
    description:
      "Indicates user has been deleted from the system and it will be logged out ",
    type: "Warning",
  },
  {
    statusCode: 124,
    statusName: "RESETPASSWORDFAILED",
    message: "Password could not be reset. Please try again later",
    description: "Indicated that due to some reason password reset got failed.",
    type: "Failure",
  },
  {
    statusCode: 125,
    statusName: "USERPASSWORDCHANGE",
    message:
      "Your account password has been changed. You will be logged out within 10 seconds.",
    description:
      "Indicates that the user will be logged out as Administrator has changed user account password.",
    type: "Warning",
  },
  {
    statusCode: 126,
    statusName: "USERDISABLED",
    message:
      "Your user account is disabled from system.You will be logged out immediately",
    description:
      "Indicates user has been disabled from the system and it will be logged out \n",
    type: "Warning",
  },
  {
    statusCode: 127,
    statusName: "DUPLICATEENTRYNOTALLOWED",
    message: "Duplicate values are not allowed in the field",
    description: "When user enters duplicate value in a unique field",
    type: "Error",
  },
  {
    statusCode: 128,
    statusName: "FMANDATORYFIELDMISSING",
    message: "Mandatory\n",
    description:
      "Frontend validation for mandatory field\n//<Field Label> : Mandatory",
    type: "Error",
  },
  {
    statusCode: 129,
    statusName: "FALREADYEXISTS",
    message: "Already Exists",
    description:
      "Fronend validation for duplicate fields\n//<Field Label> : Already Exists",
    type: "Error",
  },
  {
    statusCode: 130,
    statusName: "REQUESTTIMEOUT",
    message: "Request timed out. Please try again",
    description: "While requesting if timeout occurred",
    type: "Warning",
  },
  {
    statusCode: 131,
    statusName: "REQUIREDWEAKSECURITYFORPASSWORD",
    message: "New Password must contain 8 characters with at least 1 Alphabet",
    description: "Indicates that Password must contain mandatory characters.",
    type: "Failure",
  },
  {
    statusCode: 132,
    statusName: "INVALIDIMAGE",
    message: "Invalid image format",
    description:
      "While creating a site in case if user upload invalid site image",
    type: "Error",
  },
  {
    statusCode: 133,
    statusName: "DELETECONFORMATION",
    message: "Are you sure? You want to delete",
    description: "Delete confirmation",
    type: "Warning",
  },
  {
    statusCode: 134,
    statusName: "EDITCONFORMATION",
    message: "Are you sure? You want to save the changes",
    description: "Edit confirmation",
    type: "Information",
  },
  {
    statusCode: 135,
    statusName: "STARTIPANDENDIPDIFFERENT",
    message: "Start IP Address and End IP Address should be different",
    description: "While doing ONVIF discovery, Start IP & End IP can't be same",
    type: "Error",
  },
  {
    statusCode: 136,
    statusName: "SAMESUBNETINSTARTIPANDENDIP",
    message: "Start IP Address and End IP Address should be in same subnet",
    description:
      "While doing ONVIF discovery, Start IP & End IP should be in same subnet",
    type: "Error",
  },
  {
    statusCode: 137,
    statusName: "SEARCHISINPROGRESS",
    message: "Search is in progress",
    description: "When it takes more time in searching the records",
    type: "Information",
  },
  {
    statusCode: 138,
    statusName: "STARTTIMELESSTHANENDTIME",
    message: "Start Time should be less than End Time",
    description:
      "While creating schedule, start time should be less than end time",
    type: "Error",
  },
  {
    statusCode: 139,
    statusName: "RUNTIMEGREATORTHANCURRENTTIME",
    message: "Please enter Run time greater than current time",
    description:
      "While adding report schedule with Frequency = Once, If user selects date of schedule run day once as current date and schedule run time less than or equal to current time of system.",
    type: "Error",
  },
  {
    statusCode: 140,
    statusName: "SELECTCURRENTORFUTUREDATE",
    message: "Please select current day or future date ",
    description:
      "While adding report schedule with Frequency = Once, if user select past date",
    type: "Error",
  },
  {
    statusCode: 141,
    statusName: "KPICHANGECONFORMATION",
    message: "Are you sure you want to change the KPI?",
    description: "KPI Change Conformation",
    type: "Warning",
  },
  {
    statusCode: 142,
    statusName: "ZONEFOREACHSENSORREQUIRED",
    message: "Please add at least 1 zone for each sensor",
    description:
      "User needs to add at least one zone for each sensor, before proceeding further with the configuration",
    type: "Error",
  },
  {
    statusCode: 143,
    statusName: "NOTIFICATIONREQFORQUEUEEXCEEDED",
    message:
      "Please configure at least one real time notification in case of Queue Exceeded",
    description: "Real time notification is mandatory for Queue Exceeded",
    type: "Error",
  },
  {
    statusCode: 144,
    statusName: "SELECTUSERFORINSIGHTSSHARING",
    message: "Please select at least 1 user to which the insight to be shown",
    description:
      "In case if user turns ON any insight & do not select any user to which this insight to be shown",
    type: "Error",
  },
  {
    statusCode: 145,
    statusName: "STREAMDISCONNECTED",
    message: "Stream Disconnected. Please try again",
    description:
      "When live-view of a sensor is being fetched but due to some reason stream got disconnected",
    type: "Error",
  },
  {
    statusCode: 146,
    statusName: "SENSOROFFLINE",
    message: "Sensor Offline. Please try again later",
    description:
      "When live-view of a sensor is being fetched but sensor is offline",
    type: "Error",
  },
  {
    statusCode: 147,
    statusName: "ERRORRECEIVINGSTREAM",
    message: "Error in receiving stream",
    description:
      "Indicates that an error occurred in receiving stream from camera.",
    type: "Error",
  },
  {
    statusCode: 148,
    statusName: "ALEASTONEREALTIMENOTIFICATION",
    message: "Please configure at least one real time notification",
    description:
      "User needs to configure at least one real time notification to proceed further",
    type: "Error",
  },
  {
    statusCode: 149,
    statusName: "COUNTERFORSENSORREQUIRED",
    message: "Please add at least 1 Counter for each sensor",
    description:
      "User needs to add at least one counter for sensor, before saving configuration",
    type: "Error",
  },
  {
    statusCode: 150,
    statusName: "RECORDSAREBEINGFETCHED",
    message: "Records are being fetched, Please wait...",
    description: "When fetching of records is taking time",
    type: "Information",
  },
  {
    statusCode: 159,
    statusName: "AUTHENTICATIONFAILED",
    message: "Authentication Failed.",
    description:
      "In case if user tries to add camera/NVR and its authentication failed due to any reason",
    type: "Failure",
  },
  {
    statusCode: 154,
    statusName: "INVALIDFILEFORMAT",
    message: "Invalid file format",
    description:
      "When user tries to upload invalid file format while importing users or while uploading video file as sensor",
    type: "Failure",
  },
];
