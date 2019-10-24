
$(readyFunction);

function readyFunction(){

    const refreshTimetabling = async roomKey => {
        const field = document.querySelector("#mapp-next-booking")
        field.classList.remove("visible")
        field.textContent = ``

        let resp = await fetch("https://timetabling.business-school.ed.ac.uk/api/v1/buildings/18/locations")
        if (!resp.ok) {
            console.error("Timetabling location resp not OK", resp)
            return
        }

        const locations = await resp.json()
        const room = locations.data.find(d => d.attributes.identifier === roomKey)
        if (!room) {
            console.error("Timetabling could not find room", locations)
            return
        }

        resp = await fetch(room.relationships.bookings.links.related)
        if (!resp.ok) {
            console.error("Timetabling room bookings resp not OK", resp)
            return
        }

        const bookings = await resp.json()
        if (bookings.data.length === 0) {
            console.error("Timetabling room bookings has no bookings", bookings)
            return
        }

        const firstBooking = bookings.data.reduce((e1,e2) => (e1.attributes.start < e2.attributes.start ? e1 : e2))
        const title = firstBooking.attributes.meeting_title
        const startTime = firstBooking.attributes.start
        const endTime = firstBooking.attributes.end

        field.classList.add("visible")
        field.textContent = `${dateFns.distanceInWordsToNow(startTime, { addSuffix: true })} - ${firstBooking.attributes.meeting_title}`
    }

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
    var centreMap = function (smooth) {
        var myDiv = $("#mapscroll");
        var scrolltoh = (myDiv.prop('scrollHeight') - myDiv.height()) /2;
        var scrolltow = (myDiv.prop('scrollWidth') - myDiv.width()) /2;

        if (smooth) {
            var myDiv = $("#mapscroll");
            var scrolltoh = (myDiv.prop('scrollHeight') - myDiv.height()) /2;
            var scrolltow = (myDiv.prop('scrollWidth') - myDiv.width()) /2;
            myDiv.animate({scrollTop: scrolltoh, scrollLeft: scrolltow});
        } else {
            myDiv.scrollTop(scrolltoh);
            myDiv.scrollLeft(scrolltow);
        }
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
            const time = new Date(data.last_update * 1000);
            $("#mapp-last-update").attr("title", `Last update performed at ${dateFns.format(time)}`);
            $("#mapp-last-update > span").text(dateFns.distanceInWordsToNow(time, { addSuffix: true }));

            $("#mapp-buddybar-here").html("");
            $("#mapp-buddybar-elsewhere").html("");

            const here_count = data.friends_here_count;
            const else_count = data.friends_elsewhere_count;

            $("#mapp-here-count").text(here_count);
            $("#mapp-elsewhere-count").text(else_count);

            const {cascaders_here_count, cascaders_elsewhere_count} = data;

            let cascaders_here_msg = "No cascaders are in this room.";
            let cascaders_elsewhere_msg = "No cascaders elsewhere.";

            if (cascaders_here_count > 0) {
                cascaders_here_msg = `${cascaders_here_count} cascader${cascaders_here_count == 1 ? "" : "s"}`;
            }

            if (cascaders_elsewhere_count > 0) {
                cascaders_elsewhere_msg = `${cascaders_elsewhere_count} cascader${cascaders_elsewhere_count == 1 ? "" : "s"}`;
            }

            const base_cascaders_buddy = `
                <tr><td><small>
                    <a href="#" data-toggle="modal" data-target="#csc-mdl" class="text-cascaders">$content</a>
                </small></td></tr>`
            $("#mapp-buddybar-here").append(base_cascaders_buddy.replace("$content", cascaders_here_msg));
            $("#mapp-buddybar-elsewhere").append(base_cascaders_buddy.replace("$content", cascaders_elsewhere_msg));

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

                    let gpuSuffix = "";
                    if (cell.gpu == "True") {
                        gpuSuffix = " (gpu)"
                    }
                    text.text(cell.hostname + gpuSuffix);

                    let iconClass = "fa-television";
                    let tdClass = "";
                    let userAt = "";

                    if (cell.status === "offline") {
                        tdClass = "muted";
                    } else if (cell.cascader) {
                        iconClass = "fa-smile-o text-cascaders"
                        userAt = cell.cascader;
                    } else if (cell.friend) {
                        iconClass = "fa-hand-peace-o text-info"
                        userAt = cell.friend;
                    } else if (cell.user) {
                        tdClass = "text-danger";
                    } else if (cell.status === "online") {
                        icon.addClass("text-success");
                    } else {
                        iconClass = "fa-question-circle"
                        icon.addClass("text-warning");
                    }

                    icon.find("i").addClass(iconClass);
                    td.addClass(tdClass);

                    td.append(icon);
                    td.append(text);

                    if (userAt) {
                        const f = $(`<p class='text-${cell.cascader ? "cascaders" : "info"} userat-name'></p>`)
                        f.text(userAt);
                        td.append(f);
                    }

                    tr.append(td);
                }

                tab.append(tr);
            }

            centreMap();
            loadMapScroll();
            refreshData();

            refreshTimetabling(data.room.key).catch(err => {
                console.error("Timetabling issue:", err)
            })

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
                timestamp : Date.now()
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
        console.log(`Changing room to ${room_key}...`);
        gtag('set', 'page', location.pathname);
        gtag('send', 'pageview');

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
        centreMap(true);
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

    cascadersReady();
};

function cascadersReady() {
    const btnSave = document.getElementById("csc-save");
    const btnToggle = document.getElementById("csc-toggle");
    const inputTagline = document.getElementById("csc-tagline");
    const tableList = $("#csc-tbl");

    const ui = {
        spinnerHTML: `<i class="fa fa-spinner fa-spin"></i>`,

        getTagline: () => inputTagline.value,
        setTagline: tagline => inputTagline.value = tagline || "",
        setToggleState: enabled => {
            btnToggle.innerText = enabled ? "Stop" : "Start";
            btnToggle.classList.remove("btn-secondary", "btn-warning");
            btnToggle.classList.add(enabled ? "btn-warning" : "btn-secondary");
        },
        setToggleLoading: () => btnToggle.innerHTML = ui.spinnerHTML,
        getToggleState: () => btnToggle.innerText === "Stop",

        showError: () => alert("Failed to update. Please try again later."),
    }

    const save = async (enabled, tagline) => {
        const body = {enabled, tagline};
        const response = await fetch("/api/cascaders/me", {
            method: "POST",
            credentials: "same-origin",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(body),
        });

        return response.ok;
    }

    const updateList = () => {
        // const response = await fetch("/api/cascaders");
        // const json = await response.json();

    }

    // When the modal is shown, refresh the UI
    $("#csc-mdl").on("show.bs.modal", async () => {
        const response = await fetch("/api/cascaders/me", {credentials: "same-origin"});
        const json = await response.json();

        ui.setTagline(json['tagline']);
        ui.setToggleState(json['enabled']);

        // Update list
        tableList.bootstrapTable('refresh', {silent: true})

        // Hack to fix the fa-sync icon not appearing
        $('.bootstrap-table button[title="Refresh"]').text("Refresh");
    })

    btnToggle.addEventListener("click", () => {
        const enabled = !ui.getToggleState();
        ui.setToggleLoading();

        save(enabled, ui.getTagline()).then(success => {
            if (!success) {
                ui.showError();
                return;
            }

            ui.setToggleState(enabled);
        });
    });

    btnSave.addEventListener("click", () => {
        const oldText = btnSave.innerText;
        btnSave.innerHTML = ui.spinnerHTML;

        save(ui.getToggleState(), ui.getTagline()).then(success => {
            btnSave.innerText = oldText;

            if (!success) {
                ui.showError();
            }
        })
    })

    tableList.bootstrapTable({
        url: "/api/cascaders",
        search: true,
        sortable: true,
        showRefresh: true,
        escape: true,
        columns: [{
            field: "name",
            title: "Name"
        }, {
            field: "room",
            title: "Room",
        }, {
            "field": "tagline",
            "title": "Tagline",
        }]
    })
}
