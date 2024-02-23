// Call the dataTables jQuery plugin
$(document).ready(function() {
    var headText = $('.head').text();
    $('#dataTable').DataTable( {
        dom: "<'row'<'col-sm-12 col-md-6'l><'col-sm-12 col-md-6'f>>" +
        "<'row'<'col-sm-12'tr>>" +
        "<'row'<'col-sm-12 col-md-5'i><'text-center'p>>",
    } );

    // alternative kalau id nya dalam 1 html
    $('#dataTable1').DataTable( {
         dom: "<'row'<'col-sm-12 col-md-6'l><'col-sm-12 col-md-6'f>>" +
        "<'row'<'col-sm-12'tr>>" +
        "<'row'<'col-sm-12 col-md-5'i><'text-center'p>>",
        scrollY: '215px',
        paging: false,
    } );

    // khusus table ada image
    $('#dataTable1i').DataTable( {
         dom: "<'row'<'col-sm-12 col-md-6'l><'col-sm-12 col-md-6'f>>" +
        "<'row'<'col-sm-12'tr>>" +
        "<'row'<'col-sm-12 col-md-5'i><'text-center'p>>",
        scrollY: '304px',
        paging: false,
    } );


   $('#dataTable2').DataTable( {
        scrollY: '430px',
        scrollCollapse: true,
        paging: false,
    } );

   $('#dataTable3').DataTable( {
        dom:  "<'row'<'col-sm-4'B><'col-sm-4'l><'col-sm-4'f>>" +
        "<'row'<'col-sm-12'tr>>" +
        "<'row'<'col-sm-12 col-md-5'i><'text-center'p>>",
        buttons: [
            {
                extend: 'excelHtml5',
                title: headText,
                text: '<span class="btn-label"><i class="far fa-window-restore fa-fw text-white-50"></i></span>Export to Excel',
                className: 'btn btn-sm btn-labeled btn-success shadow-sm',
                filename: function(){
                    var now = new Date();
                    var year = now.getFullYear();
                    var month = ('0' + (now.getMonth() + 1)).slice(-2); // months are 0-based
                    var day = ('0' + now.getDate()).slice(-2);
                    var hour = ('0' + now.getHours()).slice(-2);
                    var minute = ('0' + now.getMinutes()).slice(-2);
                    var second = ('0' + now.getSeconds()).slice(-2);
                    return `REPORT_TOOLING_${year}${month}${day}_${hour}${minute}${second}`;
                }
            }

        ]
   });

   // data table add mass
   $('#dataTable4').DataTable( {
        scrollY: '405px',
        searching: false,
        info: false,
        ordering: false,
        scrollCollapse: true,
        paging: false,
        language: {
            zeroRecords: false,
            emptyTable: false
        }
   });

   //   hapus blank row dari hasil zeroRecords: false, emptyTable: false (scrolly function)
   $("#dataTable4 tr").each(function(){
        var isBlank = false;
        $(this).find('td').each(function(){
            if ($(this).text().trim() === '') {
                isBlank = true;
            }
        });
        if (isBlank) {
            $(this).remove();
        }
    });
});

function isNumberKey(evt) {
    var charCode = (evt.which) ? evt.which : evt.keyCode
    if (charCode > 31 && (charCode < 48 || charCode > 57))
    return false;
    return true;
}

// auto focus input tap card
 $(document).ready(function(){
      $('#id-modal').on('shown.bs.modal', function() {
          $('#uid').focus();
      });
});

// disable other input jika salah satu input di isi (sesi filter / search)
 $(document).ready(function(){
      $('#myForm input[type="text"]').on('input', function() {
          if($(this).val() !== '') {
            $('#myForm input[type="text"]').not(this).prop('disabled', true);
          } else {
            $('#myForm input[type="text"]').prop('disabled', false);
          }
      });
});

// refresh haalaman ketika tombol kembali
function preventBack(){window.history.forward();}
    window.onunload=function(){null};

// autofocus saat modal tap card muncul
 $(document).ready(function(){
      $('#id-tap').on('shown.bs.modal', function() {
          $('#uid').trigger('focus');
      });
});
