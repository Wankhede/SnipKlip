import math


def get_pagination(request,query,paginator):
    total_entries = len(query)
    page = request.GET.get('page')
    if page == "" or page == 1 or page == None:
        page = 1
    else:
        page = page

    all_data = list(query)[(paginator*(int(page)-1)):paginator*int(page)]
    start_index = (paginator*(int(page)-1))+1
    end_index = paginator*int(page)
    current_page = math.ceil(end_index / paginator)
    previous_page = current_page - 1
    next_page = current_page + 1
    num_pages = math.ceil((total_entries/paginator))

    if current_page >= 11 and current_page < (math.ceil((total_entries/paginator)+1)-12):
        
        #all index (previous 6 index number & after 6 index number from current index number)
        page_list = [x for x in range(current_page-6,current_page+6)]

        for i in range(math.ceil((total_entries/paginator)+1)-6,math.ceil(total_entries/paginator)+1):
            page_list.append(i)

        page_split = (current_page + 5)

    elif current_page >= math.ceil(((total_entries/paginator)+1)-12):
        page_list = [x for x in range(current_page-(math.ceil((total_entries/paginator)+1)-current_page),current_page-4)]
        
        for i in range(current_page,current_page+(math.ceil((total_entries/paginator)+1)-current_page)):
            page_list.append(i)

        page_split = (current_page - 5)

    elif current_page <= 11:
        page_list = [x for x in range(current_page-(current_page-1),current_page+4)]
        for i in range(math.ceil((total_entries/paginator)+1)-10,math.ceil(total_entries/paginator)+1):
            page_list.append(i)
        page_split = (current_page+4) -1 

    response = {
        'all_data':all_data,'num_pages':num_pages,'next_page':next_page,'previous_page':previous_page,'page_split':page_split,'page_list':page_list,'start_index':start_index,'current_page':current_page,'end_index':end_index,'total_entries':total_entries
    }

    return response