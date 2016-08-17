/*
 * JSBox - based on thickbox 3.1
 * By Toussaint Guglielmi (http://www.spyroland.net)
 * Thickbox originaly by Cody Lindley (http://www.codylindley.com)
 * Licensed under the MIT License: http://www.opensource.org/licenses/mit-license.php

Changes from 3.1:
- added floating arrows above the image for prev/next image
	Activate by setting the useFloatNav option to true
	This disables the ability to close by clicking the image
- added an optional navbar above the box
	Activate by setting the useNavBar option to true
- allow for galleries of anything, using the navbar for browsing
	The navbar is automatically added if viewing an iframe/ajax in a gallery
	There can be no modal in a gallery
- allow the personalisation of "close" link
	Set options.closeHTML to the html code
	The link must be of id "TB_closeWindowButton"
	See default value for example
- allow the personalisation of the "next/prev" caption (or removal)
	Set prevHTML to the html code for previous
	Set nextHTML to the html code for next
	Ids of links must be TB_prev and TB_next
- look for parameters inside the gallery names
	rel="gallery1+navbar-floatnav" => enables navbar and disables floating arrows
	Settings belong to the gallery name, so they must in every item's rel
- allow the personalisation of the "image x/y" caption
	Set options.imageXofY
	Xhere {x} is the current item and {y} the total items

- better default shortcuts (from my non-american-keyboard point of view)
- anonymous "namespace" variables
- jsbox can be added to dom elements by using $(selector).jsbox()
- configuration can be changed with jQuery.JSBox.config({ key : value})
- the caption is added to the alt attribute programatically (avoids quote collision)

TODO
- custom load images with css (so the url can be raltive to the css)
- add a command to the navbar: diaporama
- move some essential formatting from the css to $().css() here ?
- remove formatting in captions in $("#TB_image").attr("alt",caption);
- get captions somewhere else ? (see slimbox: accepts a accessor function)

*/

jQuery(function(){

// "global" variables (they are actually scoped inside this anonymous function,
// like an anonymous package, yay)
var options, globalOptions, imgLoader = new Image(), nextImgLoader = new Image(), TB_WIDTH, TB_HEIGHT, isModal;
// groups vars (1-based, not 0-based)
var theItems=null, thisItem=0, numItems=0, prevItem=0, nextItem=0;
var IMGpat = "\.(jpg|jpeg|png|gif|bmp)(\\?|$)";

// default options
options = new Array();
globalOptions = {
	// Images - loading image url / name relative to the script (or something)
	loadImage		: "thickbox-loading.gif",
	// Nav Bar Options
	useNavBar		: true,
	// Float Nav Options
	useFloatNav		: true,
	// Can zoom large images
	canZoom			: true,
	// Do we loop ?
	loop			: true,
	// Do we animate ? and how fast ?
	speed			: 0,
	// Do we animate width and height independantly
	splitResize		: false,
	// TB_window minimum width for variable content (the content is centered)
	minWidth		: 0,
	// Subtitle text
	closeHTML		: "<a href='#' title='Close'>close</a> or Esc Key",//	 in #TB_closeWindow
	prevHTML		: "&nbsp;&nbsp;<a href='#'>&lt; Prev</a>&nbsp;&nbsp;",// in #TB_prev
	nextHTML		: "&nbsp;&nbsp;<a href='#'>Next &gt;</a>&nbsp;&nbsp;",// in #TB_next
	imageXofY		: "Image {x} / {y}",
	hasCaption		: true,
	hasSubText		: true,
	// keys
	closeKeys		: [27], // [esc]
	nextKeys		: [39], // [->]
	prevKeys		: [37], // [<-]
	zoomKeys		: [ 9], // [tab]
	// overlayCaption
	overlayCaption	: ""//"Click in the background to close"
};

// jsbox object
// since all the rest is private to the anonymous englobing function,
// this is like the public API, needed
jQuery.JSBox = {
	config		:	config,
	initialize	:	initialize,
	show		:	showBox,
	close		:	close,
	previous	:	goPrev,
	next		:	goNext,
	page		:	goItem,
	showIframe	:	showIframe
};

// add jsbox to selected DOM elements
function bindBox(domChunk){
	jQuery(domChunk).click(function(){
		showBox(this);
		this.blur();
		return false;
	});
}
// add jsbox as a plugin
jQuery.fn.extend({
	jsbox: function() {
		return this.each(function() { bindBox(this); });
	}
});

// ################################################################
// #################### jsbox methods ##########################
// configuration method (to change the options)
function config(the_options){
	if (the_options) jQuery.extend(globalOptions, the_options);
	imgLoader.src = globalOptions.loadImage;
}
// initialize function (default classes to apply jsbox to)
function initialize(){
	// Initial config (preloads the loadImage)
	jQuery.JSBox.config(null);
	// Apply jsbox to some ".jsbox" classes and ".thickbox" for retro compatibility
	jQuery('a.thickbox, area.thickbox, input.thickbox, a.jsbox, area.jsbox, input.jsbox').jsbox();
}

// ################################################################
// #################### Main display functions ####################
// ################################################################

// #################### Show the Box ##############################
// function called when the user clicks on a jsbox link
// or directly called to display an item
function showBox(element, the_options, fullsize){
try{
	// get the element properties
	isModal = false;
	var caption = (element.title || ""),
		url = (element.href || element.src || element.alt),
		itemGroup = (jQuery(element).attr("rel") || ""),
		groupName = (itemGroup.match("^[^-+]+") || "");
	
	// if we start a new galery (or single item)
	if(numItems==0) {
		// blend the options: options < globalOptions < the_options
		jQuery.extend(options, globalOptions);
		if(typeof the_options != "undefined") jQuery.extend(options, the_options);
		// preload the loading image (if changed)
		imgLoader.src = options.loadImage;
		// get the group options (if it is a group)
 		if(itemGroup.match("\\+|-")){
 			if(itemGroup.indexOf('+navbar')>=0) options.useNavBar=true;
 			if(itemGroup.indexOf('-navbar')>=0) options.useNavBar=false;
 			if(itemGroup.indexOf('+floatnav')>=0) options.useFloatNav=true;
 			if(itemGroup.indexOf('-floatnav')>=0) options.useFloatNav=false;
 			if(itemGroup.indexOf('+loop')>=0) options.loop=true;
 			if(itemGroup.indexOf('-loop')>=0) options.loop=false;
 			if(itemGroup.indexOf('+caption')>=0) options.hasCaption=true;
 			if(itemGroup.indexOf('-caption')>=0) options.hasCaption=false;
 			if(itemGroup.indexOf('+subtext')>=0) options.hasSubText=true;
 			if(itemGroup.indexOf('-subtext')>=0) options.hasSubText=false;
 			if((m=itemGroup.match("(\\+|-)speed=(\\d+)")) != null) options.speed=m[2];
 		}
	}
	// setup the group and item context	
	if(groupName.length>0) {
		if(numItems==0){
			theItems = jQuery("*[rel="+itemGroup+"]");
			numItems = theItems.length;
		}
		thisItem = theItems.index(element)+1;
		prevItem = (thisItem > 1 ? thisItem-1 : (options.loop ? numItems : 0));
		nextItem = (thisItem < numItems ? thisItem+1 : (options.loop ? 1 : 0));
	} else {
		thisItem=1; numItems=1;
		prevItem=0; nextItem=0;
		theItems = jQuery(element);
	}

	// Create / configure the overlay if necessary
	// contains hack for IE6, to hide select with iframe
	if(jQuery("#TB_overlay").size() == 0){
		// common code
		jQuery("body").append('<div id="TB_overlay"></div>');
		jQuery("#TB_overlay").click(close);
		// starting position
		top = (jQuery(document).scrollTop()+jQuery(window).height()/2-20);
		left = (jQuery(document).scrollLeft()+jQuery(window).width()/2-20);
		jQuery('<div id="TB_window"></div>').hide().css({
			position:"absolute",
			top : top +"px",height:"40px",
			left: left+"px",width:"40px"
		}).appendTo("body");
		// FF mac Hack
		if(detectMacXFF()){
			jQuery("#TB_overlay").addClass("TB_overlayMacFFBGHack"); //use png overlay to hide flash
		}else{
			jQuery("#TB_overlay").addClass("TB_overlayBG"); //use background and opacity
		}
	}

	// add and show loader
	jQuery("body").append("<div id='TB_load'></div>");
	//jQuery('#TB_load').append("<img src='"+options.loadImage+"' />");
	jQuery('#TB_load').show();
	
	// Keydown configuration
	document.onkeydown = function(e){
		if (e == null){ keycode = event.keyCode; }	//ie
		else { keycode = e.which; }					//mozilla
		if($.inArray(keycode, options.closeKeys) >= 0) { close();  return false; }
		if($.inArray(keycode, options.prevKeys)  >= 0) { goPrev(); return false; }
		if($.inArray(keycode, options.nextKeys)  >= 0) { goNext(); return false; }
		if($.inArray(keycode, options.zoomKeys)  >= 0) { doZoom(); return false; }
		return true;
	};
	
	// #############
	// Show an image
	if(url.toLowerCase().match(IMGpat)) {
		showImage(url, caption, fullsize);
	}else{
	// Show some html or link
		showHtml(url, caption);
	}
	// #############
	// NOTE: showHtml() can change the isModal and useNavBar options
	
	// preload next image (AFTER loading current item)
	if(nextItem > 0) {
		var nextPreload, nextPreloadUrl, nextPreloadImage;
		nextPreload = theItems[nextItem-1];
		nextPreloadUrl = (nextPreload.href || nextPreload.src || nextPreload.alt);
		if(nextPreloadUrl.toLowerCase().match(IMGpat)) {
			nextPreloadImage = new Image();
			nextPreloadImage.src = nextPreloadUrl;
		}
	}
	
	// Nav Bar
	displayNavBar();
	// No key bindings in a modal
	if(isModal){ document.onkeydown = ""; }
	// Overlay Caption
	if(options.overlayCaption && !isModal && jQuery("#TB_overlayCaption").size() == 0){
		jQuery("#TB_overlay").append('<div id="TB_overlayCaption">'+options.overlayCaption+'</div>');
	}
}catch(e){ alert(e); }
}
// #################### /Show the Box #############################

// #################### Display an image ##########################
function showImage(url, caption, fullsize){
	if((fullsize!==false) && (fullsize!==true)) { fullsize=false; }
	var image_padding = options.useNavBar?90:10;
	imgPreloader = new Image();
	imgPreloader.onload = function(){
		imgPreloader.onload = null;
		// Resizing large images
		// original by Christian Montoya
		var x = jQuery(window).width();
		var y = jQuery(window).height() - image_padding;
		var imageWidth = imgPreloader.width;
		var imageHeight = imgPreloader.height;
		if (imageWidth > x) {
			imageHeight = imageHeight * (x / imageWidth);
			imageWidth = x;
			if (imageHeight > y) {
				imageWidth = imageWidth * (y / imageHeight);
				imageHeight = y;
			}
		} else if (imageHeight > y) {
			imageWidth = imageWidth * (y / imageHeight);
			imageHeight = y;
			if (imageWidth > x) {
				imageHeight = imageHeight * (x / imageWidth);
				imageWidth = x;
			}
		}
		var resized = !(imageWidth==imgPreloader.width && imageHeight==imgPreloader.height);
		if(resized && fullsize) {
			// the image should be resized but won't
			imageWidth = imgPreloader.width;
			imageHeight= imgPreloader.height;
		}
		// END Resizing large images
		
		// Minimum width (centers the image)
		real_imageWidth = imageWidth;
		if(typeof options.minWidth != "undefined") {
			if(imageWidth < options.minWidth) imageWidth = options.minWidth;
		}
		
		TB_WIDTH = imageWidth;// + 30;
		TB_HEIGHT = imageHeight;// + 60;

		// ##### Compose the image and surrounds html to add to the TB_window
		// #### ADD image (invisible for the animation)
		//jQuery("#TB_window").remove("#TB_imageBloc").append('<div id="TB_imageBloc"></div>');
		if(jQuery("#TB_imageBloc").length == 0) {
			jQuery("#TB_window").append('<div id="TB_imageBloc"></div>');
		}
		var tbImg = jQuery('#TB_imageBloc').css({width:imageWidth, height:imageHeight, position: "relative", margin:"auto"})
			.append(jQuery("<img id='TB_image' src='"+url+"' />").attr("alt", caption)
					.css({width:real_imageWidth, height:imageHeight, margin:"auto", display:"block"})
			).css({opacity:0, filter:"alpha(opacity=0)"});
		// close box on clicking on single image (not gallery)
		if(numItems==1) tbImg.click(close).css({cursor:"pointer"}).attr("title","close");
		
		// #### ADD Floating navigation images
		if(options.useFloatNav && prevItem) {
			jQuery("#TB_imageBloc").append('<a href="#" id="TB_floatPrev"> </a>');
			jQuery("#TB_floatPrev").css({"left": 0,"top": 0, "width": imageWidth*2/5+"px", "height":imageHeight+"px"}).click(goPrev);
		}
		if(options.useFloatNav && nextItem) {
			jQuery("#TB_imageBloc").append('<a href="#" id="TB_floatNext"> </a>');
			jQuery("#TB_floatNext").css({"right": 0,"top": 0, "width": imageWidth*2/5+"px", "height":imageHeight+"px"}).click(goNext);
		}
		// ### ADD Floating zooming links
		if(options.canZoom && resized) {
			jQuery("#TB_floatZoom").remove();
			jQuery("#TB_imageBloc").append('<a href="#" id="TB_floatZoom"> </a>');
			if(fullsize) {
				jQuery("#TB_floatZoom").addClass("zoomout");
			} else {
				jQuery("#TB_floatZoom").addClass("zoomin");
			}
			jQuery("#TB_floatZoom").click(doZoom);
		}
		
		// make sure we see everything if needed
		jQuery('#TB_window').css("overflow","visible");
		// #### ADD the caption under the image
		jQuery("#TB_window").remove("#TB_caption");
		if(caption && options.hasCaption)
			jQuery("#TB_window").append("<div id='TB_caption'>"+caption+"</div>");
		// #### ADD the sub text
		if(options.hasSubText){
			jQuery("#TB_window").remove("#TB_subText").append('<div id="TB_subText"></div>');
			jQuery("#TB_subText,#TB_caption").css({opacity:0, filter:"alpha(opacity=0)"});
			var tbwinHTML = "";
			if(numItems>1){  // add navigation text + links, if not empty
				var secondLine="",imageXofY="";
				if(typeof options.imageXofY == "function") {
					imageXofY = options.imageXofY(thisItem,numItems);
				} else {
					imageXofY = options.imageXofY.replace("{x}",thisItem).replace("{y}",numItems);
				}
				if(imageXofY) secondLine += '<span id="TB_imageXofY">'+imageXofY+'</span>';
				if(prevItem)  secondLine += '<span id="TB_prev">'+options.prevHTML+'</span>';
				if(nextItem)  secondLine += '<span id="TB_next">'+options.nextHTML+'</span>';
				if(secondLine) tbwinHTML += "<div id='TB_secondLine'>" + secondLine + "</div>";
			}
			if(options.closeHTML)// add navigation and close links
				tbwinHTML += "<div id='TB_closeWindow'>" + options.closeHTML + "</div>";
			jQuery("#TB_subText,#TB_caption").css({width:imageWidth, margin:"auto"});
			jQuery("#TB_subText").append(tbwinHTML);
		}
		
		// display (animating)
		position(TB_WIDTH,TB_HEIGHT + (options.hasSubText?30:0));
		jQuery("#TB_window").queue(function(){
			jQuery('#TB_imageBloc').animate({opacity:1,filter:"alpha(opacity=100)"},250*options.speed);
			jQuery("#TB_window").css({height:"auto"});
			jQuery("#TB_subText,#TB_caption").css({opacity:1,filter:"alpha(opacity=100)"});
			jQuery("#TB_subText,#TB_caption").slideDown(0*400*options.speed).queue(function(){
				//delta = jQuery(window).height()/2 +TB_HEIGHT/2 -jQuery("#TB_window").height();
				//if(delta<=0) position(TB_WIDTH,jQuery("#TB_window").height());
				jQuery(this).dequeue();
			})
			jQuery("#TB_load").remove(); // remove loading image
			jQuery(this).dequeue();
		});

		// Buttons/Links bindings
		jQuery("#TB_closeWindow a").click(close);
		jQuery("#TB_prev a").click(goPrev);
		jQuery("#TB_next a").click(goNext);

		jQuery("#TB_window").css({display:"block"}); //for safari using css instead of show
	};
	imgPreloader.src = url;
}

// #################### display some html #########################
function showHtml(url, caption){
	var queryString = url.replace(/^[^\?]+\??/,'');
	var params = parseQuery( queryString );
	
	TB_WIDTH = (params['width']*1) + 30 || 630; //defaults to 630 if no paramaters were added to URL
	TB_HEIGHT = (params['height']*1) + 40 || 440; //defaults to 440 if no paramaters were added to URL
	ajaxContentW = TB_WIDTH - 30;
	ajaxContentH = TB_HEIGHT - 45;
	
	// make sure you can browse through items, no modal in a gallery
	if(numItems>1) options.useNavBar=true;
	if(numItems==1 && params['modal']=="true") isModal = true;

	position(TB_WIDTH,TB_HEIGHT);
	
	if(url.indexOf('TB_iframe') != -1){// either iframe or ajax window
		urlNoQuery = url.split('TB_');
		jQuery("#TB_iframeContent").remove();
		if(!isModal){//iframe no modal : window bar
			jQuery("#TB_window").append("<div id='TB_title'><div id='TB_ajaxWindowTitle'>"+caption+"</div><div id='TB_closeAjaxWindow'>"+options.closeHTML+"</div></div>");
		}else{//iframe modal
			jQuery("#TB_overlay").unbind();
		}
		jQuery("#TB_window").append("<iframe frameborder='0' hspace='0' src='"+urlNoQuery[0]+"' id='TB_iframeContent' name='TB_iframeContent"+Math.round(Math.random()*1000)+"' onload='jQuery.JSBox.showIframe()' style='width:"+(ajaxContentW + 29)+"px;height:"+(ajaxContentH + 17)+"px;'> </iframe>");
	}else{// not an iframe, ajax
		if(jQuery("#TB_ajaxContent").size()==0){
			if(!isModal){//ajax no modal
				jQuery("#TB_window").append("<div id='TB_title'><div id='TB_ajaxWindowTitle'>"+caption+"</div><div id='TB_closeAjaxWindow'>"+options.closeHTML+"</div></div>");
			}else{//ajax modal
				jQuery("#TB_overlay").unbind();
			}
			jQuery("#TB_window").append("<div id='TB_ajaxContent' class='TB_modal' style='width:"+ajaxContentW+"px;height:"+ajaxContentH+"px;'></div>");
		}else{//this means the window is already up, we are just loading new content via ajax
			jQuery("#TB_ajaxContent")[0].style.width = ajaxContentW +"px";
			jQuery("#TB_ajaxContent")[0].style.height = ajaxContentH +"px";
			jQuery("#TB_ajaxContent")[0].scrollTop = 0;
			jQuery("#TB_ajaxWindowTitle").html(caption);
		}
	}
	
	jQuery("#TB_closeWindowButton").click(close);
	
	if(url.indexOf('TB_inline') != -1){
		jQuery("#TB_ajaxContent").append(jQuery('#' + params['inlineId']).children());
		jQuery("#TB_window").unload(function () {
			jQuery('#' + params['inlineId']).append( jQuery("#TB_ajaxContent").children() ); // move elements back when you're finished
		});
		position(TB_WIDTH,TB_HEIGHT);
		jQuery("#TB_load").remove();
		jQuery("#TB_window").css({display:"block"});
	}else if(url.indexOf('TB_iframe') != -1){
		position(TB_WIDTH,TB_HEIGHT);
		// if($.browser.safari){
		//safari needs help because it will not fire iframe onload
		jQuery("#TB_load").remove();
		jQuery("#TB_window").css({display:"block"});
	}else{
		jQuery("#TB_ajaxContent").load(url += "&random=" + (new Date().getTime()),function(){
		//to do a post change this load method
			position(TB_WIDTH,TB_HEIGHT);
			jQuery("#TB_load").remove();
			bindBox("#TB_ajaxContent a.thickbox, #TB_ajaxContent a.jsbox");
			jQuery("#TB_window").css({display:"block"});
		});
	}
}
// #################### /display some html ########################

// ################################################################
// #################### close, goprev & gonext ####################
// Close the Box
function close(){
	theItems=null; thisItem=0; numItems=0; prevItem=0; nextItem=0;
 	jQuery("#TB_image").unbind("click");
	jQuery("#TB_closeWindowButton").unbind("click");
	jQuery("#TB_window, #TB_overlay, #TB_hideSelect, #TB_navBar").fadeOut(options.speed>0?"fast":1, function(){jQuery('#TB_window, #TB_overlay, #TB_hideSelect, #TB_navBar')	.trigger("unload").unbind().remove();});
	jQuery("#TB_load").remove();
	//typeof document.body.style.maxHeight == "undefined"
	document.onkeydown = "";
	return false;
}
// Go to the previous item
function goPrev(){
	if(prevItem){ goItem(prevItem); }
	return false;
}
// Go to the following item
function goNext(){
	if(nextItem){ goItem(nextItem); }
	return false;
}
// Go to the previous item
function goItem(i, zoom){
	if(i>0 && i<=numItems){
		document.onkeydown = "";
		imgPreloader.onload = null;
		jQuery("#TB_window,#TB_window *").stop(true);
		jQuery("#TB_load").remove();
		jQuery("#TB_window").animate({height: TB_HEIGHT+"px"}, 200*options.speed).trigger("unload").unbind().empty();
		showBox(theItems[i-1],{},zoom);
	}
	return false;
}

// ################################################################
// #################### generic helpers ###########################
// Overlay creation
function detectMacXFF() {
	var userAgent = navigator.userAgent.toLowerCase();
	if (userAgent.indexOf('mac') != -1 && userAgent.indexOf('firefox')!=-1) {
		return true;
	}
	return false;
}
// Position and resize the TB window
function position(pwidth,pheight) {
	var tmin = (globalOptions.useNavBar && numItems>1) ? 32:2,
		lmin = 2,
		left  = (jQuery(document).scrollLeft()+Math.max(lmin,(jQuery(window).width()-pwidth)/2)) +'px',
		width = pwidth +"px",
		top   = (jQuery(document).scrollTop()+Math.max(tmin,(jQuery(window).height()-pheight)/2)) +'px',
		height= pheight+"px";
	
	if(options.splitResize) {
		jQuery("#TB_window")
		.animate({left: left, width: width}, 200*options.speed)
		.animate({top: top, height: height}, 200*options.speed);
	} else {
		jQuery("#TB_window")
		.animate({left: left, width: width, top: top, height: height}, 200*options.speed);
	}
}
// Resize the image to full size
function doZoom(){
	if(jQuery("#TB_floatZoom").size()>0) {
		var i =  thisItem;
		var zoom = jQuery("#TB_floatZoom").hasClass("zoomin");
		goItem(thisItem, zoom);
	}
	return false;
}
// Display the Nav Bar
function displayNavBar() {
	if(options.useNavBar && !isModal && (numItems>1)) {
		jQuery("#TB_navBar").remove();
		jQuery("body").append('<div id="TB_navBar"></div>');
		jQuery('#TB_navBar')
			.append('<a id="TB_navBarClose" href="#"></a>')
			.append('<div id="TB_navBarMiddle"></div>');
		if(numItems>1) {
			jQuery("#TB_navBarMiddle")
			.append('<a id="TB_navBarPrev" href="#"></a>')
			.append('<span id="TB_navBarCaption">' + (thisItem) + '&nbsp;/&nbsp;' + (numItems) + '</span>')
			.append('<a id="TB_navBarNext" href="#"></a>')
		}
		jQuery("#TB_navBarClose").click(close);
		if(prevItem) jQuery("#TB_navBarPrev").css("cursor","pointer").click(goPrev); else jQuery("#TB_navBarPrev").hide();
		if(nextItem) jQuery("#TB_navBarNext").css("cursor","pointer").click(goNext); else jQuery("#TB_navBarNext").hide();
	} else { // should not be necessary
		jQuery("#TB_navBar").remove();
	}
}

// ################################################################
// #################### loadHTML helpers ##########################
function showIframe(){
	jQuery("#TB_load").remove();
	jQuery("#TB_window").css({display:"block"});
}
function parseQuery ( query ) {
   var Params = {};
   if ( ! query ) {return Params;}// return empty object
   var Pairs = query.split(/[;&]/);
   for ( var i = 0; i < Pairs.length; i++ ) {
      var KeyVal = Pairs[i].split('=');
      if ( ! KeyVal || KeyVal.length != 2 ) {continue;}
      var key = unescape( KeyVal[0] );
      var val = unescape( KeyVal[1] );
      val = val.replace(/\+/g, ' ');
      Params[key] = val;
   }
   return Params;
}

// ################################################################
// ############ Initialize jsbox for real #####################
jQuery.JSBox.initialize();

}); // end pageload thingy
