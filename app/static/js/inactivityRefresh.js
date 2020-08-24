 var time = new Date().getTime();
 $(document.body).bind("mousemove keypress", function(e) {
     time = new Date().getTime();
 });

 function refresh() {
     if(new Date().getTime() - time >= 45000)
         location.replace('signin');
     else
         setTimeout(refresh);
 }

 setTimeout(refresh);