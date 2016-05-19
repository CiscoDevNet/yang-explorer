from django.shortcuts import render


def yangctx(request):

    if request.method == 'POST':

        return render(request, 'yangctx/yangctx.html', {'message': 'POST'})

    else:

        return render(request, 'yangctx/yangctx.html', {'message': 'GET'})
