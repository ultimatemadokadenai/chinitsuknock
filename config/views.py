from django.shortcuts import render, redirect, get_object_or_404
from .models import Room
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import random
from mahjong.tile import TilesConverter
from mahjong.hand_calculating.hand import HandCalculator
from mahjong.hand_calculating.hand_config import HandConfig

calculator = HandCalculator()
correct_waiting_tiles = []

# --- ホスト作成 ---
def host_room(request):
    if request.method == "POST":
        player_name = request.session.get('player_name', '匿名')
        while True:
            room_id = str(random.randint(100, 999))
            if not Room.objects.filter(room_id=room_id).exists():
                break
        room = Room.objects.create(room_id=room_id, host_name=player_name, players=json.dumps([player_name]))
        return redirect('room_detail', room_id=room_id)
    return render(request, 'config/host_room.html')

def host_create(request):
    player_name = request.session.get('player_name')
    if not player_name:
        return redirect('enter_name')

    # 3桁のユニークな部屋番号を生成
    while True:
        room_id = str(random.randint(100, 999))
        if not Room.objects.filter(room_id=room_id).exists():
            break

    # ルーム作成
    room = Room.objects.create(room_id=room_id)
    room.players = [player_name]  # 仮に文字列で保存している場合
    room.save()

    return redirect('host_room', room_id=room_id)

# --- 入室 ---
def join_room(request):
    if request.method == "POST":
        room_id = request.POST.get('room_id')
        player_name = request.session.get('player_name', '匿名')
        try:
            room = Room.objects.get(room_id=room_id)
            room.add_player(player_name)
            return redirect('room_detail', room_id=room_id)
        except Room.DoesNotExist:
            return render(request, 'config/join_room.html', {'error': "部屋がありません"})
    return render(request, 'config/join_room.html')

# --- 部屋詳細 ---
def room_detail(request, room_id):
    room = get_object_or_404(Room, room_id=room_id)
    players = room.get_players()
    return render(request, 'config/room_detail.html', {
        'room_id': room_id,
        'players': players,
        'is_host': room.host_name == request.session.get('player_name')
    })

def enter_name(request):
    return render(request, 'config/enter_name.html')

def set_name(request):
    if request.method == 'POST':
        name = request.POST.get('player_name')
        request.session['player_name'] = name
        return redirect('index')
    return redirect('enter_name')

# --- 清一色生成・待ち判定 ---
def generate_tiles():
    tiles = [str(i) for i in range(1, 10)] * 4
    hand = []
    while len(hand) < 13:
        candidate = random.choice(tiles)
        if hand.count(candidate) < 4:
            hand.append(candidate)
    hand.sort()
    return hand

def check_waiting_tiles(hand):
    waiting_tiles = []
    hand_str = ''.join(hand)
    for tile_num in range(1, 10):
        if hand.count(str(tile_num)) >= 4:
            continue
        test_hand_str = hand_str + str(tile_num)
        tiles = TilesConverter.string_to_136_array(man=test_hand_str)
        win_tile_index = len(tiles) - 1
        try:
            result = calculator.estimate_hand_value(
                tiles, win_tile_index, melds=None, dora_indicators=None, config=HandConfig()
            )
            if result.error is None:
                waiting_tiles.append(tile_num)
        except:
            continue
    return waiting_tiles

# --- トップページ ---
def index(request):
    name = request.session.get('player_name')
    return render(request, 'config/index.html', {'player_name': name})

# --- シングルプレイ ---
def single_mode(request):
    global correct_waiting_tiles
    hand = generate_tiles()
    correct_waiting_tiles = check_waiting_tiles(hand)
    return render(request, 'config/single_mode.html', {
        'hand': hand,
        'waiting_tiles': correct_waiting_tiles
    })

# --- クイズの回答チェック（Ajax） ---
@csrf_exempt
def check_answer(request):
    global correct_waiting_tiles
    if request.method == "POST":
        data = json.loads(request.body)
        selected = list(map(int, data.get('selected', [])))
        correct = sorted(selected) == sorted(correct_waiting_tiles)
        return JsonResponse({
            'correct': correct,
            'answer': correct_waiting_tiles
        })

# --- マルチプレイ選択画面 ---
def multi_select(request):
    return render(request, 'config/multi_select.html')

# --- ホスト待機画面 ---
def host_room(request):
    room_id = generate_unique_room_id()
    return render(request, 'config/host_room.html', {'room_id': room_id})

# --- 入室画面 ---
def join_room(request):
    return render(request, 'config/join_room.html')

# --- ユニークな3桁ルームIDを生成する補助関数 ---
def generate_unique_room_id():
    # 実際はデータベースと照合すべきだが、ここではランダム生成だけ
    return str(random.randint(100, 999))
