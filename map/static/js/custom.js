$(function(){
    var clicked = false, clickY, clickX;
    /**
    *Self Centering function
    */
    (function(){ 
        var myDiv = $("#mapscroll");
        var scrolltoh = (myDiv.prop('scrollHeight') - myDiv.height()) /2;
        var scrolltow = (myDiv.prop('scrollWidth') - myDiv.width()) /2;
        myDiv.scrollTop(scrolltoh);
        myDiv.scrollLeft(scrolltow);
    })();

    var smoothCentreMap = function () {
        var myDiv = $("#mapscroll");
        var scrolltoh = (myDiv.prop('scrollHeight') - myDiv.height()) /2;
        var scrolltow = (myDiv.prop('scrollWidth') - myDiv.width()) /2;
        myDiv.animate({scrollTop: scrolltoh, scrollLeft: scrolltow});
    };

    var zoomBox = function () {
        var myDiv = $("#mapscroll");
    }
     var updateScrollPos = function(e) {
        $('html').css('cursor', 'move');
        $("#mapscroll").scrollTop(iPosY - (e.pageY - clickY));
        $("#mapscroll").scrollLeft(iPosX - (e.pageX - clickX));
    }
    $(this).on({
        'mousemove': function(e) {
             clicked && updateScrollPos(e);
        },
        'mousedown': function(e) {
            if(e.which == 1){
                clicked = true;
                clickY = e.pageY;
                clickX = e.pageX;
                iPosY = $("#mapscroll").scrollTop();
                iPosX = $("#mapscroll").scrollLeft();
            }
        },
        'mouseup': function() {
            clicked = false;
            $('html').css('cursor', 'auto');
        }
    });
});
