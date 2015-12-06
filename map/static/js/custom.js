
$(function(){
    //Move function expressions to top because hoisting doesn't work for them
    var clicked = false, clickY, clickX,
        regexName = /^([a-zA-Z]+( )*)+$/, //Fucked up regex, somebody pls fix it
        $zoomIn = $('#zoom-in'),
        $zoomOut = $('#zoom-out'),
        $zoomCenter = $('#center-map'),
        $mapScroll = $('#mapscroll'),
        $friendName = $("#new-friend"),
        $nameError = $('#name-error-alert'),
        $selectError = $('#select-error-alert'),
        $friendList = $('#friend-list'),
        $addButton = $('#add-btn'),
        $removeButton = $('#remove-btn');

    var renderFriendList = function(data){
        var friends = data['friendList'],
            htmlOptions = '';
        if (friends.length > 0){
            $('#del-form').removeClass('hidden');
            $('#no-friends').addClass('hidden');
            friends.forEach(function(value){
                htmlOptions+='<option>'+value+'</option>'
            })
            $friendList.html(htmlOptions);
            if (friends.length === 1)
                $removeButton.text("Remove Friend");
            else
                $removeButton.text("Remove Friend(s)");
        }
        else {
            $('#del-form').addClass('hidden');
            $('#no-friends').removeClass('hidden');            
        }
    };
     var centreMap = function () {
        var myDiv = $("#mapscroll");
        var scrolltoh = (myDiv.prop('scrollHeight') - myDiv.height()) /2;
        var scrolltow = (myDiv.prop('scrollWidth') - myDiv.width()) /2;
        myDiv.scrollTop(scrolltoh);
        myDiv.scrollLeft(scrolltow);
    };

    var smoothCentreMap = function () {
        var myDiv = $mapScroll.get(0);
        var scrolltoh = (myDiv.prop('scrollHeight') - myDiv.height()) /2;
        var scrolltow = (myDiv.prop('scrollWidth') - myDiv.width()) /2;
        myDiv.animate({scrollTop: scrolltoh, scrollLeft: scrolltow});
    };
    var mapZoom = function  (multiplier, start) {
        if ($mapScroll.css('font-size') == "") {
            $mapScroll.css({'font-size':'15px'});
        }

        if (typeof start === "undefined"){
            start = $mapScroll.css('font-size');
        }
        
        var newsize = parseFloat(start) + (multiplier * 1) + "px";
        $mapScroll.css({'font-size' : newsize});
    };
    var updateScrollPos = function(e) {
        $('html').css('cursor', 'move');
        $mapScroll.scrollTop(iPosY - (e.pageY - clickY));
        $mapScroll.scrollLeft(iPosX - (e.pageX - clickX));
    };
     var mapUpdate = function(){
         $.ajax({ 
            url: '/refresh' 
        })
         .done(function(data){
             $('#ajax-map-replace').replaceWith(data);   
              centreMap();
        });
    };
    var checkRefreshAvailable = function(){
            var timeNow = new Date();
            $.ajax({
                url: '/update_available',
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({
                    timestamp : timeNow.toJSON().replace('Z','')
                }),
                dataType:'json'
            })
            .done(function(data) {
                if(data['status'] != 'False') {
                   mapUpdate();
                }
            });       
    };

/* Execute, self */
    $.ajax({
        url: '/friends'
    }).done(function(data) {
            renderFriendList(data);
    });
    
    centreMap();

   window.setInterval(checkRefreshAvailable,30000);
/*Listeners*/
    
    $zoomIn.on('click',function(){
        mapZoom(1)
    });
    $zoomOut.on('click',function(){
        mapZoom(-1)
    });
    $zoomCenter.on('click',function(){
        mapZoom(0,'15px');
        centreMap();
    });
    $mapScroll.on({
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
        if ($friendList.find('option:selected')['length']>0){ //Check selections aren't empty
            $selectError.addClass('hidden');
             $.ajax({
                url: '/friends',
                type: 'POST',
                data: $(this).serialize()
            })
             .done(function(data) {
                    renderFriendList(data);
            });
        }
        else {
            if ($selectError.hasClass('hidden'))
                $selectError.removeClass('hidden')
            $selectError.html("No Option Selected!")
        }
    });

    $('#add-form').on('submit',function(e){
        e.preventDefault();
        if ($friendName.val().match(regexName) != null){
            $nameError.addClass('hidden');
            $.ajax({
                url: '/friends',
                type: 'POST',
                data: $(this).serialize()
            })
                .done(function(data) {
                    $friendName.val(''); //Reset the form!
                    renderFriendList(data);
                });
        }
        else {
            if ($nameError.hasClass('hidden'))
                $nameError.removeClass('hidden');
            $nameError.html('Invalid Name!');
        }
    });

    $('#friends-dropdown').on('hide.bs.dropdown',function(){
        $nameError.addClass('hidden');
        $selectError.addClass('hidden');
        $('.dropdown-toggle').blur(); // Removes the focus from the Manage friends after close
    });

    /* Listeners to add a Nice slide transition to dropdowns */

    $('.dropdown').on('show.bs.dropdown', function(e){
        $(this).find('.dropdown-menu').first().stop(true, true).fadeIn("slow");
    });

   $('.dropdown').on('hide.bs.dropdown', function(e){
        $(this).find('.dropdown-menu').first().stop(true, true).fadeOut("slow");
    });

});


