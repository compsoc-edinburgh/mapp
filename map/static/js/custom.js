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
    //Default call on startup
    $.ajax({
        url: '/friends'
    })
    .done(function(data) {
        renderFriendList(data);
    });

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

    /* form handling ajaxes */
    $('#del-form').on('submit',function(e){
        e.preventDefault();
        $.ajax({
            url: '/friends',
            type: 'POST',
            data: $(this).serialize()
        })
        .done(function(data) {
            renderFriendList(data);
        });
        
    });

    $('#add-form').on('submit',function(e){
        e.preventDefault();
        $.ajax({
            url: '/friends',
            type: 'POST',
            data: $(this).serialize()
        })
        .done(function(data) {
            $("#new-friend").val(''); //Reset the form!
            renderFriendList(data);
        });
    });

    var renderFriendList = function(data){
        var friends = data['friendList'],
            htmlOptions = '';
        if (friends.length > 0){
            $('#del-form').removeClass('hidden');
            $('#no-friends').addClass('hidden');
            friends.forEach(function(value){
                htmlOptions+='<option>'+value+'</option>'
            })
            $('#friend-list').html(htmlOptions);
            if (friends.length === 1)
                $('#remove-btn').text("Remove Friend");
            else
                $('#remove-btn').text("Remove Friend(s)");
        }
        else {
            $('#del-form').addClass('hidden');
            $('#no-friends').removeClass('hidden');            
        }

    }
});
