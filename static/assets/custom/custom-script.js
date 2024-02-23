// create row
$(document).ready(function() {

    // add newline (mass)
    $('#my-btn3').on('click', function() {
        var qty = $('#qty-row').val();
        for (var i = 0; i < qty; i++) {
            $('.myTable tbody').append(
            '<tr class="child">'+
            '<th id="numb" class="align-middle"></th>'+
            '<td><input class="form-control form-control-sm shadow-none my-paste" type="text" id="no_loc" name="no_loc" required/></td>'+
            '<td><input class="form-control form-control-sm shadow-none my-paste" type="text" id="prod_code" name="prod_code" required/></td>'+
            '<td><input class="form-control form-control-sm shadow-none my-paste" type="number" min=0 id="qty" name="qty" onkeypress="return isNumberKey(event)" required/></td>'+
            '<td class="text-center align-middle"><input type="checkbox" name="record"></td>'+
            '</tr>'
            );
        }
    });

    // add receipt
    $('#my-btn').on('click', function() {
        var qty = $('#qty-row').val();
        for (var i = 0; i < qty; i++) {
           $('.myTable tbody').append('<tr class="child">'+
           '<th id="numb" class="align-middle"></th>'+
           '<td><input class="form-control form-control-sm my-paste" id="no_ttb" type="text" name="no_ttb" required/></div></td>'+
           '<td><input class="form-control form-control-sm my-paste" id="vendor" type="text" name="vendor" required/></td>'+
           // '<td><input class="form-control form-control-sm my-paste" id="date" type="text" name="date" required/></td>'+
           '<td><input class="form-control form-control-sm my-paste" id="no_pr" type="text" name="no_pr" required/></td>'+
           '<td><input class="form-control form-control-sm my-paste" type="text" id="prod_code" name="prod_code" required/></td>'+
           '<td><input class="form-control form-control-sm my-paste" type="text" id="prod_desc" name="prod_desc" required/></td>'+
           '<td><input class="form-control form-control-sm my-paste" min=1 type="number" id="qty" name="qty" placeholder=0 required/></td>'+
           '<td class="text-center align-middle"><input type="checkbox" name="record"></td></tr>');
        }
    });

    // add location (mass)
    $('#my-btn1').on('click', function() {
        var qty = $('#qty-row').val();
        for (var i = 0; i < qty; i++) {
            $('.myTable tbody').append(
            '<tr class="child">'+
            '<th id="numb" class="align-middle"></th>'+
            '<td><input class="form-control form-control-sm my-paste" type="text" id="no_loc" name="no_loc" required/></td>'+
            '<td><input class="form-control form-control-sm my-paste" type="text" id="assign" name="assign" required/></td>'+
            '<td><input class="form-control form-control-sm my-paste" type="text" id="storage" name="storage" required/></td>'+
            '<td><input class="form-control form-control-sm my-paste" type="text" id="area" name="area" required/></td>'+
            '<td class="text-center align-middle"><input type="checkbox" name="record"></td>'+
            '</tr>'
            );
        }
    });

    // add product (mass)
    $('#my-btn2').on('click', function() {
        var qty = $('#qty-row').val();
        for (var i = 0; i < qty; i++) {
            $('.myTable tbody').append(
            '<tr class="child">'+
            '<th id="numb" class="align-middle"></th>'+
            '<td><input class="form-control form-control-sm my-paste" type="text" id="prod_code" name="prod_code" required/></td>'+
            '<td><input class="form-control form-control-sm my-paste" type="text" id="prod_desc" name="prod_desc" required/></td>'+
            '<td><input class="form-control form-control-sm my-paste" type="text" id="uom" name="uom" required/></td>'+
            '<td><input class="form-control form-control-sm my-paste" type="number" min="1" id="pack_size" name="pack_size" placeholder=0 onkeypress="return isNumberKey(event)" required/></td>'+
            '<td><input class="form-control form-control-sm my-paste" type="number" min="1" id="stock_min" name="stock_min" placeholder=0 onkeypress="return isNumberKey(event)" required/></td>'+
            '<td><input class="form-control form-control-sm my-paste" type="number" min="1" id="stock_max" name="stock_max" placeholder=0 onkeypress="return isNumberKey(event)" required/></td>'+
            '<td><input class="form-control form-control-sm my-paste" type="number" min="1" id="l_time_days" name="l_time_days" placeholder="0" onkeypress="return isNumberKey(event)" required/></td>'+
            '<td><input class="form-control form-control-sm my-paste" type="text" id="supplier" name="supplier" required/></td>'+
            '<td class="text-center align-middle"><input type="checkbox" name="record"></td>'+
            '</tr>'
            );
        }
    });

    // paste automatically table
    $('body').on('paste', '.my-paste', function (e) {
        var $start = $(this);
        var source

        //check for access to clipboard from window or event
        if (window.clipboardData !== undefined) {
            source = window.clipboardData
        } else {
            source = e.originalEvent.clipboardData;
        }
        var data = source.getData("Text");
        if (data.length > 0) {
            if (data.indexOf("\t") > -1) {
                var columns = data.split("\n");
                $.each(columns, function () {
                    var values = this.split("\t");
                    $.each(values, function () {
                        $start.val(this);
                        if ($start.closest('td').next('td').find('input')[0] != undefined || $start.closest('td').next('td').find('textarea')[0] != undefined) {
                        $start = $start.closest('td').next('td').find('input');
                        }
                        else
                        {
                         return false;
                        }
                    });
                    $start = $start.closest('td').parent().next('tr').children('td:first').find('input');
                });
                e.preventDefault();
            }
        }
    });

    // Find and remove selected table rows
    $(".delete-row").click(function(){
        $("table tbody").find('input[name="record"]').each(function(){
            if($(this).is(":checked")){
                $(this).parents("tr").remove();
            }
        });
    });

    // ganti nama di element browse file image
    $('#image-upload').on('change',function(){
        //get the file name
        var fileName = $(this).val();
        //replace the "Choose a file" label
        $(this).next('.custom-file-label').html(fileName);
    })
});

// preview image before upload
/* function previewFile(input){
    var file = $("input[type=file]").get(0).files[0];

    if(file){
        var reader = new FileReader();

        reader.onload = function(){
            $("#previewImg").attr("src", reader.result).height(200).width(300).addClass('border');
        }

        reader.readAsDataURL(file);
    }
}
*/

function previewImage(event) {
    var input = event.target;

    if (input.files && input.files[0]) {
        var reader = new FileReader();

        reader.onload = function (e) {
            var img = new Image();
            img.src = e.target.result;

            img.onload = function () {
                var aspectRatio = 4 / 3;
                var canvas = document.createElement('canvas');
                var ctx = canvas.getContext('2d');

                if (img.width / img.height > aspectRatio) {
                    var newWidth = img.height * aspectRatio;
                    canvas.width = newWidth;
                    canvas.height = img.height;
                    ctx.drawImage(img, (img.width - newWidth) / 2, 0, newWidth, img.height, 0, 0, newWidth, img.height);
                } else {
                    var newHeight = img.width / aspectRatio;
                    canvas.width = img.width;
                    canvas.height = newHeight;
                    ctx.drawImage(img, 0, (img.height - newHeight) / 2, img.width, newHeight, 0, 0, img.width, newHeight);
                }
                document.getElementById('image-preview').src = canvas.toDataURL('image/jpeg');
            };
        };
        reader.readAsDataURL(input.files[0]);
    }
}

$(document).ready(function() {
    $('#superuserCheckbox').change(function() {
        if ($(this).is(':checked')) {
            // If superuser checkbox is checked, set both is_superuser and is_staff to true
            $('input[name="is_superuser"]').val('true');
            $('input[name="is_staff"]').val('true');
        } else {
            // If superuser checkbox is unchecked, clear both is_superuser and is_staff
            $('input[name="is_superuser"]').val('');
            $('input[name="is_staff"]').val('');
        }
    });
});

