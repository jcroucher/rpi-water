function delete_zone(zone_id)
{
    if( confirm("Are you sure you want to delete this zone?") )
    {
        window.location = '/deletezone/?zone=' + zone_id;
    }
}

function delete_program(program_id)
{
    if( confirm("Are you sure you want to delete this program?") )
    {
        window.location = '/deleteprogram/?program=' + program_id;
    }
}