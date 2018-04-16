
$(readyFunction);

function readyFunction(){
    //Move function expressions to top because hoisting doesn't work for them
    var clicked = false, clickY, clickX,
        regexName = /^([a-zA-Z]+\ [A-Za-z]+)$/,
        $selectError = $('#select-error-alert'),
        $friendList = $('#friend-list'),
        $addButton = $('#add-btn'),
        $removeButton = $('#remove-btn'),
        $roomList = $('#room-list'),
        roomList,
        $refreshAlert =  $('#refresh-alert-holder');

    var renderFriendList = function(data){
        var friends = data['friendList'];

        $friendList.empty();

        if ((friends != null) && (friends.length > 0)){
            $('#del-form').removeClass('d-none');
            $('#no-friends').addClass('d-none');

            friends.forEach(function(value){
                $friendList.append($("<option>", {
                    text: value[0],
                    'data-uun': value[1]
                }));
            })

            if (friends.length === 1)
                $removeButton.text("Remove Friend");
            else
                $removeButton.text("Remove Friends");
        }
        else {
            $('#del-form').addClass('d-none');
            $('#no-friends').removeClass('d-none');            
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
        var myDiv = $("#mapscroll");
        var scrolltoh = (myDiv.prop('scrollHeight') - myDiv.height()) /2;
        var scrolltow = (myDiv.prop('scrollWidth') - myDiv.width()) /2;
        myDiv.animate({scrollTop: scrolltoh, scrollLeft: scrolltow});
    };
    var mapZoom = function  (multiplier, start) {
        myDiv = $("#mapscroll");
        if (myDiv.css('font-size') == "") {
            myDiv.css({'font-size':'15px'});
        }

        if (typeof start === "undefined"){
            start = myDiv.css('font-size');
        }
        
        var newsize = parseFloat(start) + (multiplier * 1) + "px";
        myDiv.css({'font-size' : newsize});
    };
    var updateScrollPos = function(e) {
        $('html').css('cursor', 'move');
        var myDiv = $("#mapscroll");
        myDiv.scrollTop(iPosY - (e.pageY - clickY));
        myDiv.scrollLeft(iPosX - (e.pageX - clickX));
    };

    let mapRotation = 0;
    var updateRotation = function() {
        $(".mapp-table").css("transform", `rotate(${mapRotation}deg)`);
        $(".mapp-table td").css("transform", `rotate(-${mapRotation}deg)`);
        $("#rotation-indicator").css("transform", `rotate(${mapRotation}deg)`);
    }

    $("#rotate-map").on("click", () => {
        mapRotation += 180;
        updateRotation();
    });

    var timeNow
    var useCache = true;

    // Needs to be updated in css as well, find `fadeClasses`
    const fadeClasses = ".tabwrap, .mapp-pane-header > div, .mapp-pane-friends > table";

    var mapUpdate = function(){
        timeNow = new Date();
        var parts = location.pathname.split('/');
        var site = parts.pop() || parts.pop();  // handle potential trailing slash

        $.ajax({
            url: `/api/refresh?site=${site}`,
            cache: useCache,
        })
        .done(function(data){
            console.log(data);

            $("#mapp-room-name").text(data.room.name);
            $("#mapp-num-free")
                .text(data.num_free)
                .removeClass("text-warning").removeClass('text-success')
                .addClass(data.low_availability ? "text-warning" : "text-success");
            $("#mapp-num-machines").text(data.num_machines);
            $("#mapp-last-update-parent").attr("title", `Last update performed at ${data.last_update}`);
            $("#mapp-last-update").text(data.last_update);

            $("#mapp-buddybar-here").html("");
            $("#mapp-buddybar-elsewhere").html("");

            const here_count = data.friends_here_count;
            const else_count = data.friends_elsewhere_count;
            if (here_count === 0) {
                $("#mapp-buddybar-here").append("<tr><td><small>No friends are in this room.</small></td></tr>");
            }

            if (else_count === 0) {
                $("#mapp-buddybar-elsewhere").append("<tr><td><small>No friends elsewhere.</small></td></tr>");
            }

            for (let i in data.friends) {
                const f = data.friends[i];

                const tr = $("<tr><td/></tr>");
                const td = $(tr.children()[0])
                let listID = "#mapp-buddybar-here";
                td.text(f.name);
                if (!f.here) {
                    listID = "#mapp-buddybar-elsewhere";

                    const sm = $("<small> (<a/>)</small>");
                    sm.find("a").text(f.room_key).attr("href", `/site/${ f.room_key }`);
                    sm.on('click', () => {
                        switchRoom(f.room_key, true);
                        return false;
                    })
                    td.append(sm);
                }

                $(listID).append(tr);
            }

            const tab = $(".mapp-table > tbody");
            tab.html(""); // reset inner html
            for (let i in data.rows) {
                const row = data.rows[i];

                const tr = $("<tr/>");

                for (let j in row) {
                    const cell = row[j];
                    const td = $("<td/>");

                    if (!cell.hostname) {
                        tr.append(td);
                        continue;
                    }

                    const icon = $("<p class=blip><i class=fa></i></p>")
                    const text = $("<p></p>");

                    text.text(cell.hostname);

                    let iconClass = "fa-television";
                    let tdClass = "";
                    let userAt = "";

                    if (cell.status === "offline") {
                        tdClass = "muted";
                    } else if (cell.friend) {
                        iconClass = "fa-hand-peace-o text-info"
                        userAt = cell.friend;
                    } else if (cell.user) {
                        tdClass = "text-danger";
                    } else {
                        icon.addClass("text-success");
                    }

                    icon.find("i").addClass(iconClass);
                    td.addClass(tdClass);

                    td.append(icon);
                    td.append(text);

                    if (userAt) {

                        const f = $("<p class='text-info userat-name'></p>")
                        f.text(cell.friend);
                        td.append(f);
                    }

                    tr.append(td);
                }

                tab.append(tr);
            }

            centreMap();
            loadMapScroll();
            refreshData();

            setTimeout(() => $(fadeClasses).animate({ opacity: 1 }));
        });
    };
    var createRefreshAlert = function (status) {
        var statusString = '   <strong>Update available!</strong> Updating map...';
        if (status == 'False')
            statusString = '  <strong>No update available!</strong>';
        $refreshAlert.html('<div class="alert alert-info fade show" role=alert> ' + statusString + '</div>');

        window.setTimeout(function(){
            $('#manual-refresh').prop('disabled',false);
            $refreshAlert.find('.alert').alert('close');
        }, 3000);
    };
    var checkRefreshAvailable = function(){
        $.ajax({
            url: '/api/update_available',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                timestamp : timeNow.toJSON().replace('Z','')
            }),
            dataType:'json'
        })
            .done(function(data) {
                createRefreshAlert(data['status']);
                if(data['status'] != 'False') {
                    useCache = false;
                    mapUpdate();
                }
            });       
    };
    var loadMapScroll = function() {
        $("#mapscroll").on({
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
    }

    var refreshData = function() {
        /* Execute, self */
        $.ajax({
            url: '/api/friends'
        }).done(function(data) {
            renderFriendList(data);
        });
    }

    var switchRoom = function(room_key, pushState) {
        mapRotation = 0;
        updateRotation();

        $.when($(fadeClasses).animate({ opacity: 0 })).then(() => {
            if (pushState) {
                const title = `${room_key} :: Marauder's Mapp`;
                history.pushState({ room_key: room_key }, title, `/site/${room_key}`)
                document.title = title;
            }

            useCache = true;
            mapUpdate();
        })
    }

    $(window).on("popstate", e => {
        const state = e.originalEvent.state;
        if (typeof state == "object") {
            if (state.room_key) {
                switchRoom(state.room_key);
            }
        }
    })

    var performSearch = () => {
        $.ajax({
            url: '/api/search',
            type: 'GET',
            data: {
                'name': $searchFriendInput.val(),
            }
        }).done(data => {
            $searchFriendList.find('option').remove();
            for (let i in data.people) {
                const name = data.people[i].name;
                const uun = data.people[i].uun;
                const friend = data.people[i].friend === true;

                const opt = $("<option></option>").text(`${name} (${uun})`).data("uun", uun);
                opt.dblclick(addSearchedFriend);
                if (friend) {
                    opt.attr("disabled", true)
                }

                $searchFriendList.append(opt);
            }
        })
    }

    var addSearchedFriend = () => {
        const selected = $searchFriendList.find("option:selected");
        if (selected[0] === undefined) {
            return;
        }

        $.ajax({
            url: '/api/friends',
            type: 'POST',
            data: {
                'type': 'add',
                'uun': $(selected[0]).data('uun'),
            }
        })
        .done(function(data) {
            renderFriendList(data);
            performSearch();
        });
    }

    centreMap();

    // Check for a refresh every five minutes
    window.setInterval(checkRefreshAvailable, 5 * 60 * 1000);
    /*Listeners*/
    
    $('#zoom-in').on('click',function(){
        mapZoom(1)

    });
    $('#zoom-out').on('click',function(){
        mapZoom(-1)
    });
    $('#center-map').on('click',function(){
        mapZoom(0,'15px');
        centreMap();
    });
    $('#manual-refresh').on('click',function(){
        $(this).prop('disabled',true);
        checkRefreshAvailable();
    });

    if (location.pathname.startsWith("/site/") || location.pathname === "/demo") {
        $(".mapp-rooms-dropdown > a").on('click', function() {
            const room_key = $(this).data('room-key');
            switchRoom(room_key, true);
            $(".mapp-rooms-dropdown > a.active").removeClass('active');
            $(`.mapp-rooms-dropdown > a[data-room-key="${ room_key }"]`).addClass("active");
            $(".mapp-rooms-dropdown").dropdown('toggle');
            return false;
        })
    }

    $addButton.on('click',function(){
        $(this).blur();
    });
    $removeButton.on('click',function(){
        $(this).blur();
    });
    loadMapScroll();

    /* form handling ajaxes */
    $('#del-form').on('submit',function(e){
        e.preventDefault();
        if ($friendList.find('option:selected')['length']>0){ //Check selections aren't empty
            $selectError.addClass('d-none');
            const delfriends = $("#friend-list").find(":selected").toArray().map((o) => $(o).data('uun'));

            $.ajax({
                url: '/api/friends',
                type: 'POST',
                data: {
                    delfriends: delfriends,
                    type: 'del',
                },
            })
                .done(function(data) {
                    renderFriendList(data);
                    performSearch();
                });
        }
        else {
            if ($selectError.hasClass('d-none'))
                $selectError.removeClass('d-none')
            $selectError.html("<i class=\"fa fa-warning\"></i></i><span class=\"spacer\"></span> No friends selected")
        }
    });


    $searchFriendInput = $("#search-friend-input");
    $searchFriendList = $("#search-friend-list");
    $('#add-form').on('submit',function(e){
        e.preventDefault();

        performSearch();
    });

    $("#add-btn").on('click', addSearchedFriend);
    $("#search-btn").on('click', performSearch);

    $('.dropdown').on('hide.bs.dropdown',function(){
        $selectError.addClass('d-none');
        $('.dropdown-toggle').blur(); // Removes the focus from the Manage friends after close
    });

    /* Listeners to add a Nice slide transition to dropdowns */
    
    $('.dropdown').on('show.bs.dropdown', function(e){
        $(this).find('.dropdown-menu').first().stop(true, true).fadeIn("fast");
    });
    
    $('.dropdown').on('hide.bs.dropdown', function(e){
        $(this).find('.dropdown-menu').first().stop(true, true).fadeOut("fast");
    });
    
    mapUpdate();
};


