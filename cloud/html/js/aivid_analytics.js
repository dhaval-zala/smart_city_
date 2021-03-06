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
  var colors_label = { person: "red", vehicle: "cyan", bike: "lime" };

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
      console.log("Received Data", data.response);
      var timed = {};
      var duration = 180; //static

      var is_opera =
        window.navigator.userAgent.indexOf("OPR") > -1 ||
        window.navigator.userAgent.indexOf("Opera") > -1;
      var is_edge = window.navigator.userAgent.indexOf("Edge") > -1;
      var is_chrome = !!window.chrome && !is_opera && !is_edge;
      var offset = is_chrome ? 0 : doc._source.start_time * 1000; //0 initially

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

            $.each(timed[tid], function (x, v) {
              $.each(v._source.objects, function (x1, v1) {
                if ("detection" in v1 && v1.roi_type == "person") {
                  if ("bounding_box" in v1.detection) {
                    var xmin = v1.detection.bounding_box.x_min * sw;
                    var xmax = v1.detection.bounding_box.x_max * sw;
                    var ymin = v1.detection.bounding_box.y_min * sh;
                    var ymax = v1.detection.bounding_box.y_max * sh;
                    if (xmin != xmax && ymin != ymax) {
                      // var id = "id" in v1 ? ":#" + v1.id + ":" : ":";
                      var id = v1.detection.id;
                      // var track_id = "track_id" in v1 ? v1.track_id + ":" : ":";
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
