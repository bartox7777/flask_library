function switch_select_input(select, input, input_label, button, input_inner, select_inner){
    select.hidden = !select.hidden;
    input_label.hidden = input.hidden = !input.hidden;

    if (select.hidden){
        button.innerHTML = input_inner;
        input.required = true;
    } else{
        input.value = "";
        input.required = false;
        button.innerHTML = select_inner;
    }
}