 var time = new Date().getTime();
 $(document.body).bind("mousemove keypress", function(e) {
     time = new Date().getTime();
 });

 function refresh() {
     if(new Date().getTime() - time >= 10000)
         location.replace('dashboard');
     else
         setTimeout(refresh);
 }

 setTimeout(refresh);