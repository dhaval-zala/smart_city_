function draw_analytics(video, doc) {
  var colors_id = [
    "#24693d",
    "#44914e",
    "#73ba67",
    "#ced7c3",
    "#f8816b",
    "#e33f43",
    "#a3123a",
  ];
  var colors_label = {
    person: "red",
    vehicle: "cyan",
    bike: "lime",
    Covered_Face: "red",
    Covid_Mask: "cyan",
  };
  var colorr = "red";
  apiHost
    .search(
      "analytics",
      'sensor="' +
        doc._source.sensor +
        '" and time>=' +
        doc._source.time +
        " and time<" +
        (doc._source.time + doc._source.duration * 1000),
      doc._source.office,
      10000
    )
    .then(function (data) {
      /* group time into time buckets */
      var timed = {};
      var duration = 180; //static;
      var is_opera =
        window.navigator.userAgent.indexOf("OPR") > -1 ||
        window.navigator.userAgent.indexOf("Opera") > -1;
      var is_edge = window.navigator.userAgent.indexOf("Edge") > -1;
      var is_chrome = !!window.chrome && !is_opera && !is_edge;
      var offset = is_chrome ? 0 : doc._source.start_time * 1000;
      $.each(data.response, function (x, v) {
        var tid = Math.floor(
          (v._source.time - doc._source.time - offset) / duration
        );
        if (!(tid in timed)) timed[tid] = [];
        timed[tid].push(v);
      });

      var svg = video.parent().find("svg");
      var draw = function () {
        var tid = Math.floor(
          (new Date() - video.data("time_offset")) / duration
        );
        if (tid != video.data("last_draw")) {
          video.data("last_draw", tid);

          svghtml = "";
          if (tid in timed) {
            var sx = svg.width() / video[0].videoWidth;
            var sy = svg.height() / video[0].videoHeight;
            var sxy = Math.min(sx, sy);
            var sw = sxy * video[0].videoWidth;
            var sh = sxy * video[0].videoHeight;
            var sxoff = (svg.width() - sw) / 2;
            var syoff = (svg.height() - sh) / 2;
            // console.log("------------------printing------------------", v._source);

            $.each(timed[tid], function (x, v) {
              $.each(v._source.objects, function (x1, v1) {
                if ("detection" in v1 && v1.roi_type == "person") {
                  if ("bounding_box" in v1.detection) {
                    var xmin = v1.detection.bounding_box.x_min * sw;
                    var xmax = v1.detection.bounding_box.x_max * sw;
                    var ymin = v1.detection.bounding_box.y_min * sh;
                    var ymax = v1.detection.bounding_box.y_max * sh;
                    if (xmin != xmax && ymin != ymax) {
                      
                      var id = v1.detection.id;
                      svghtml =
                        svghtml +
                        '<rect x="' +
                        (sxoff + xmin) +
                        '" y="' +
                        (syoff + ymin) +
                        '" width="' +
                        (xmax - xmin) +
                        '" height="' +
                        (ymax - ymin) +
                        '" stroke="' +
                        colors_label[v1.detection.label] +
                        '" stroke-width="1" fill="none"></rect><text x="' +
                        (sxoff + xmin) +
                        '" y="' +
                        (syoff + ymin) +
                        '" fill="cyan" font-size = "large">' +
                        (text.translate(v1.detection.label) +
                          
                          text.translate(" : ") +
                          Math.floor(v1.detection.confidence * 100) +
                          "%") +
                        "</text>";
                    }
                  }
                }
              });
                });
              // var txt = "";
              // var coords = "";
              // $.each(v._source.curr_tracked_objs, function (x_temp, v_temp) {
              //     var cx = v_temp[0] * sxy + sxoff;
              //     var cy = v_temp[1] * sxy + syoff;
              //     svghtml = svghtml + '<circle cx="' + cx + '" cy="' + cy + '" r="10" stroke="cyan" fill="black"></circle>';
              //     svghtml = svghtml + '<text x="' + (cx) + '" y="' + (cy - 10) + '" fill="cyan" font-size = "large">' + (text.translate(x_temp)) + '</text>';
              // });
              // var xxt = 10 * sxy + sxoff;
              // var yyt = (120) * sxy + syoff;
              // svghtml = svghtml + '<text x="' + (xxt) + '" y="' + (yyt) + '" fill="white" font-size = "x-large">' + (text.translate("Time = ")) + (text.translate(txt)) + '</text>';
              // var xxt = 10 * sxy + sxoff;
              // var yyt = (120) * sxy + syoff;
              // svghtml = svghtml + '<text x="' + (xxt) + '" y="' + (yyt) + '" fill="white" font-size = "x-large">' + (text.translate("Time = ")) + (text.translate(txt)) + '</text>';

              // var xxt = 10 * sxy + sxoff;
              // var yyt = (1080 - 80) * sxy + syoff;
              // svghtml = svghtml + '<text x="' + (xxt) + '" y="' + (yyt) + '" fill="white" font-size = "x-large">' + (text.translate("Person in ROI 1: ")) + (text.translate(v._source.person_in_roi1)) + '</text>';

              // var xxt = 10 * sxy + sxoff;
              // var yyt = (1080 - 120) * sxy + syoff;
              // svghtml = svghtml + '<text x="' + (xxt) + '" y="' + (yyt) + '" fill="white" font-size = "x-large">' + (text.translate("Person in ROI 2: ")) + (text.translate(v._source.person_in_roi2)) + '</text>';

              // var xxt = 10 * sxy + sxoff;
              // var yyt = (80) * sxy + syoff;
              // svghtml = svghtml + '<text x="' + (xxt) + '" y="' + (yyt) + '" fill="white" font-size = "x-large">' + (text.translate("Frame No.= ")) + (text.translate(v._source.frame_count)) + '</text>';

              // var txt = "";
              // $.each(v._source.customer_times, function (x_, v_) {
              //     txt = txt + text.translate(x_) + text.translate(": ") + text.translate(v_) + text.translate(", ")
              // });
              // var xxt = 10 * sxy + sxoff;
              // var yyt = (120) * sxy + syoff;
              // svghtml = svghtml + '<text x="' + (xxt) + '" y="' + (yyt) + '" fill="white" font-size = "x-large">' + (text.translate("Time = ")) + (text.translate(txt)) + '</text>';

              // var xxt = 10 * sxy + sxoff;
              // var yyt = (160) * sxy + syoff;
              // svghtml = svghtml + '<text x="' + (xxt) + '" y="' + (yyt) + '" fill="white" font-size = "x-large">' + (text.translate("Current tracked ppl = ")) + (text.translate(v._source.name_curr_tracked_objs)) + '</text>';

              // var xxt = 10 * sxy + sxoff;
              // var yyt = (200) * sxy + syoff;
              // svghtml = svghtml + '<text x="' + (xxt) + '" y="' + (yyt) + '" fill="white" font-size = "x-large">' + (text.translate("Current customer coord = ")) + (text.translate(v._source.curr_customer_coord_x)) + (text.translate(", ")) + (text.translate(v._source.curr_customer_coord_y)) + '</text>';

              // var xxt = 1350 * sxy + sxoff;
              // var yyt = (120) * sxy + syoff;
              // svghtml = svghtml + '<text x="' + (xxt) + '" y="' + (yyt) + '" fill="white" font-size = "x-large">' + (text.translate("Engagement status = ")) + (text.translate(v._source.EngagementStatus)) + '</text>';

              // var xxt = 1350 * sxy + sxoff;
              // var yyt = (160) * sxy + syoff;
              // svghtml = svghtml + '<text x="' + (xxt) + '" y="' + (yyt) + '" fill="white" font-size = "x-large">' + (text.translate("No. of customers inside = ")) + (text.translate(v._source.num_customers_inside_now)) + '</text>';

              // var xxt = 1350 * sxy + sxoff;
              // var yyt = (200) * sxy + syoff;
              // svghtml = svghtml + '<text x="' + (xxt) + '" y="' + (yyt) + '" fill="white" font-size = "x-large">' + (text.translate("Unattended visitor count = ")) + (text.translate(v._source.unattended_visitor_count)) + '</text>';

              // var xxt = 1350 * sxy + sxoff;
              // var yyt = (240) * sxy + syoff;
              // svghtml = svghtml + '<text x="' + (xxt) + '" y="' + (yyt) + '" fill="white" font-size = "x-large">' + (text.translate("Staff status = ")) + (text.translate(v._source.staff_status)) + '</text>';

              // var xxt = 1350 * sxy + sxoff;
              // var yyt = (280) * sxy + syoff;
              // svghtml = svghtml + '<text x="' + (xxt) + '" y="' + (yyt) + '" fill="white" font-size = "x-large">' + (text.translate("Unattended flag = ")) + (text.translate(v._source.unattended_guest)) + '</text>';
            

            roi = [[447, 44, 1217, 43, 1216, 822, 456, 827, 0]];
            for (i = 0; i < roi.length; i++) {
              var xa1 = roi[i][0] * sxy + sxoff;
              var ya1 = roi[i][1] * sxy + syoff;
              var xa2 = roi[i][2] * sxy + sxoff;
              var ya2 = roi[i][3] * sxy + syoff;
              var xa3 = roi[i][4] * sxy + sxoff;
              var ya3 = roi[i][5] * sxy + syoff;
              var xa4 = roi[i][6] * sxy + sxoff;
              var ya4 = roi[i][7] * sxy + syoff;
              var colorr = "cyan";
              svghtml =
                svghtml +
                '<polygon points="' +
                xa1 +
                "," +
                ya1 +
                "," +
                xa2 +
                "," +
                ya2 +
                "," +
                xa3 +
                "," +
                ya3 +
                "," +
                xa4 +
                "," +
                ya4 +
                '" stroke="' +
                colorr +
                '" stroke-width="3" fill="none"></polygon>';
            }
          }
          svg.html(svghtml);
        }
        if (video[0].paused) return video.data("time_offset", 0);
        requestAnimationFrame(draw);
      };

      /* start playback */
      video[0].load();
      video
        .unbind("timeupdate")
        .on("timeupdate", function () {
          var tmp = video.data("time_offset");
          video.data("time_offset", new Date() - video[0].currentTime * 1000);
          if (!tmp) draw();
        })
        .unbind("loadedmetadata")
        .on("loadedmetadata", function () {
          console.log("loadedmetadata=" + video[0].currentTime);
        })
        .unbind("loadeddata")
        .on("loadeddata", function () {
          console.log("loadeddata=" + video[0].currentTime);
        });
      video.data("time_offset", new Date() - video[0].currentTime * 1000);
      draw();
    })
    .catch(function () {
      video[0].load();
    });
}
